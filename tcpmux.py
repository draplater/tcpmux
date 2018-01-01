import asyncio
import logging
import argparse
from asyncio import StreamReader, StreamWriter
from collections import namedtuple


__description__ = "Use only one port to handle HTTP, TLS, SSH and unrecognized traffic."

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class HostAndPort(namedtuple("_", "host port")):
    @classmethod
    def from_string(cls, x: str):
        host, port = x.rsplit(":", 1)
        return cls(host, port)


def get_parser():
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("--listen", type=HostAndPort.from_string, required=True, help="listen address")
    parser.add_argument("--ssh", type=HostAndPort.from_string, help="address to which SSH traffic will be forward")
    parser.add_argument("--http", type=HostAndPort.from_string, help="address to which HTTP traffic will be forward")
    parser.add_argument("--tls", type=HostAndPort.from_string, help="address to which TLS traffic will be forward")
    parser.add_argument("--other", type=HostAndPort.from_string, required=True, help="address to which unrecognized traffic will be forward")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--buffer-size", type=int, default=1024)
    return parser


async def proxy_data(reader, writer):
    try:
        while True:
            data = await asyncio.wait_for(reader.read(args.buffer_size),
                                          args.timeout)
            if not data:
                break
            writer.write(data)
            await asyncio.wait_for(writer.drain(), args.timeout)
    except Exception as e:
        logger.error('proxy_data_task exception {}'.format(e))
    finally:
        writer.close()
        logger.debug("close connection")


class MuxHandler:
    def __init__(self, args):
        self.args = args

    async def handle(self, reader: StreamReader, writer: StreamWriter):
        feature = await reader.read(8)
        if feature[:5] == b"SSH-2" and self.args.ssh:
            dest = self.args.ssh
        elif any(feature.startswith(i)
                 for i in [b"GET ", b"POST ", b"PUT ",
                           b"DELETE ", b"TRACE ", b"CONNECT ",
                           b"OPTIONS ", b"HEAD ",
                           b"COPY ", b"MOVE "]) and self.args.http:
            dest = self.args.http
        elif feature[0:2] == b"\x16\x03" and feature[5] == 1:
            dest = self.args.tls
        else:
            dest = self.args.other

        (dst_reader, dst_writer) = await asyncio.open_connection(
            host=dest.host, port=dest.port)
        dst_writer.write(feature)
        await dst_writer.drain()
        await asyncio.wait([asyncio.ensure_future(proxy_data(reader, dst_writer)),
                            asyncio.ensure_future(proxy_data(dst_reader, writer))])


if __name__ == '__main__':
    try:
        import uvloop
        logger.info("Using uvloop.")
    except ImportError:
        logger.warning("uvloop not found.")
    else:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()
    args = get_parser().parse_args()
    handler = MuxHandler(args)
    server_coro = asyncio.start_server(handler.handle, host=args.listen.host,
                                       port=args.listen.port)
    server_task = loop.run_until_complete(server_coro)
    loop.run_forever()
