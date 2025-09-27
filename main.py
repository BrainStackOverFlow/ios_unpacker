import argparse
import logging
import os
import shutil
import struct
import sys
from collections import deque
from pathlib import Path
from pprint import pprint
from zipfile import ZipFile

import aea
import asn1
import liblzfse

import get_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(created)f:%(levelname)s:%(name)s:%(module)s:%(message)s')
handler1 = logging.StreamHandler(sys.stderr)
handler1.setFormatter(formatter)
logger.addHandler(handler1)

IM4P_MAGIC = 'IM4P'
MACHO_MAGIC = b'\xcf\xfa\xed\xfe'
LZFSE_MAGIC = b'bvx2'
NXSB_MAGIC = b'NXSB'


def is_macho(path: Path) -> bool:
	with path.open("rb") as f:
		magic_bytes = f.read(4)

	if magic_bytes == MACHO_MAGIC:
		return True
	return False


def is_lzfse(path: Path) -> bool:
	with path.open("rb") as f:
		magic = f.read(4)

	return magic == LZFSE_MAGIC


def is_apple_fs(file: Path) -> bool:
	with file.open("rb") as f:
		f.seek(0x20)
		magic_bytes = f.read(4)

	return magic_bytes == NXSB_MAGIC


class IOSFirmwareProcessor:
	def __init__(self, out_dir: Path):
		self.out_dir = out_dir.resolve()
		self.input_dir = self.out_dir / "input"
		self.ipsw_out = self.out_dir / "ipsw"
		self.aea_out = self.out_dir / "aea"
		self.im4p_out = self.out_dir / "im4p"
		self.lzfse_out = self.out_dir / "lzfse"

	def process_single(self, file: Path) -> list[Path]:
		logger.info(f"Processing {file}")
		output_files = []

		relative_path = Path(*file.relative_to(self.out_dir).parts[1:])
		logger.info(f"Relative Path {relative_path}")

		if file.is_dir():
			pass
		if file.name.endswith(".ipsw"):
			logger.info("TYPE ipsw")

			with ZipFile(file, 'r') as ipsw_zip:
				zip_members = ipsw_zip.namelist()
				for zip_member in zip_members:
					logger.info(f"Extracting {zip_member}")
					ipsw_zip.extract(zip_member, self.ipsw_out / relative_path)
			output_files = [
				Path(self.ipsw_out) / relative_path / zip_member
				for zip_member
				in zip_members
			]
		elif file.name.endswith(".aea"):
			logger.info("TYPE: aea")
			decoded_path = self.aea_out / relative_path.parent / relative_path.stem

			decoded_path.parent.mkdir(parents=True, exist_ok=True)

			with file.open('rb') as f:
				aea_key = get_key.get_key(f)

			logger.info(f"symmetric_key {aea_key}")

			with file.open('br') as in_stream, decoded_path.open("w+b") as out_stream:
				aea.decode_stream(in_stream, out_stream, symmetric_key=aea_key.key_raw)

			output_files = [decoded_path]
		elif file.name.endswith(".im4p"):
			logger.info("TYPE: im4p")

			im4p_out_dir = self.im4p_out / relative_path
			im4p_out_dir.mkdir(parents=True, exist_ok=True)

			with file.open('rb') as f:
				decoder = asn1.Decoder()
				decoder.start(f)
				_, im4p_content = decoder.read()

			if not isinstance(im4p_content, list):
				raise TypeError("im4p content must be a list")

			if len(im4p_content) < 4:
				raise ValueError("Unexpected im4p len less then 4 items")

			magic = im4p_content[0]
			im4p_type = im4p_content[1]
			description = im4p_content[2]
			raw_data = im4p_content[3]

			extra_data = im4p_content[4:]

			if magic != IM4P_MAGIC:
				raise ValueError(f"Unexpected {magic=}")

			im4p_out = im4p_out_dir / f"{description}.{im4p_type}"
			im4p_out.write_bytes(raw_data)
			output_files.append(im4p_out)

			if len(extra_data) > 0:
				im4p_extra_data_out = im4p_out_dir / f"{description}.{im4p_type}.extra"
				with im4p_extra_data_out.open("wt") as f:
					pprint(extra_data, f)
				output_files.append(im4p_extra_data_out)
		elif is_lzfse(file):
			logger.info("TYPE: lzfse")
			lzfse_out = self.lzfse_out / relative_path
			lzfse_out.parent.mkdir(parents=True, exist_ok=True)
			lzfse_out.write_bytes(liblzfse.decompress(file.read_bytes()))
			output_files.append(lzfse_out)
		elif is_apple_fs(file):
			logger.info("TYPE: apple_fs")
		elif is_macho(file):
			logger.info("TYPE: mach-o")

		output_files = list(filter(lambda outfile: not outfile.is_dir(), output_files))
		logger.info(f"New Files {output_files}")
		return output_files

	def process_all(self, input_ipsw: Path):
		input_ipsw = input_ipsw.resolve()

		self.input_dir.mkdir(parents=True, exist_ok=True)
		self.ipsw_out.mkdir(parents=True, exist_ok=True)
		self.aea_out.mkdir(parents=True, exist_ok=True)

		input_in_input_dir = self.input_dir / input_ipsw.name
		shutil.copy(input_ipsw, input_in_input_dir)

		unhandled_files = deque()
		unhandled_files.append(input_in_input_dir)
		files_without_output = []

		while len(unhandled_files) > 0:
			unhandled_file = unhandled_files.popleft()
			new_unhandled_files = self.process_single(unhandled_file)
			unhandled_files.extend(new_unhandled_files)

			if len(new_unhandled_files) == 0:
				files_without_output.append(str(unhandled_file))

		with (self.out_dir / "files_without_output.txt").open("wt") as f:
			pprint(files_without_output, f)


def dir_path(path_string: str) -> Path:
	if os.path.isdir(path_string):
		return Path(path_string)
	else:
		raise argparse.ArgumentTypeError(f"'{path_string}' is not a valid directory path.")


def create_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	parser.add_argument("--input", "-i", type=Path, help="Firmware file")
	parser.add_argument("--output", "-o", type=dir_path, help="Output Dir")
	return parser


def main():
	arg_parser = create_arg_parser()
	args = arg_parser.parse_args()

	processor = IOSFirmwareProcessor(args.output)
	processor.process_all(args.input)


main()
