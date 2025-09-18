import argparse
import logging
import os
import shutil
import sys
from collections import deque
from pathlib import Path
from zipfile import ZipFile

import aea

import get_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(created)f:%(levelname)s:%(name)s:%(module)s:%(message)s')
handler1 = logging.StreamHandler(sys.stderr)
handler1.setFormatter(formatter)
logger.addHandler(handler1)


class IOSFirmwareProcessor:
	def __init__(self, out_dir: Path):
		self.out_dir = out_dir.resolve()
		self.input_dir = self.out_dir / "input"
		self.ipsw_out = self.out_dir / "ipsw"
		self.aea_out = self.out_dir / "aea"
	
	def process_single(self, file: Path) -> list[Path]:
		logger.info(f"Processing {file}")
		output_files = []
		
		relative_path = Path(*file.relative_to(self.out_dir).parts[1:])
		print(f"{file=}")
		print(f"{relative_path=}")
		if file.name.endswith(".ipsw"):
			logger.info(f"TYPE ipsw")
			
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
			logger.info(f"TYPE: aea")
			decoded_path = self.aea_out / relative_path.parent / relative_path.stem
			print(f"{decoded_path=}")
			
			decoded_path.parent.mkdir(parents=True, exist_ok=True)
			
			with file.open('rb') as f:
				aea_key = get_key.get_key(f)
			
			logger.info(f"symmetric_key {aea_key}")
			
			with decoded_path.open("bw") as f:
				aea.decode_into(file.read_bytes(), f, symmetric_key=aea_key.key_raw)
			
			output_files = [decoded_path]
		
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
		
		while len(unhandled_files) > 0:
			unhandled_file = unhandled_files.popleft()
			new_unhandled_files = self.process_single(unhandled_file)
			unhandled_files.extend(new_unhandled_files)


def dir_path(path_string: str):
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
