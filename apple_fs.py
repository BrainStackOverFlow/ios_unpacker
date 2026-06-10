# Based on:
# https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf
import os
from contextlib import contextmanager
from pathlib import Path

from construct import Struct, Bytes, Int64ul, Int32ul, Array, this, Const, Int16ul, Construct, Container, PaddedString

PAddr = Int64ul

PRange = Struct(
	pr_start_paddr=PAddr,
	pr_block_count=Int64ul,
)

OID = Int64ul
XID = Int64ul

UUID = Bytes(16)

# Object types
OBJECT_TYPE_MASK = 0x0000ffff
OBJECT_TYPE_FLAGS_MASK = 0xffff0000

OBJECT_TYPE_NX_SUPERBLOCK = 0x00000001
OBJECT_TYPE_BTREE = 0x00000002
OBJECT_TYPE_BTREE_NODE = 0x00000003
OBJECT_TYPE_SPACEMAN = 0x00000005
OBJECT_TYPE_SPACEMAN_CAB = 0x00000006
OBJECT_TYPE_SPACEMAN_CIB = 0x00000007
OBJECT_TYPE_SPACEMAN_BITMAP = 0x00000008
OBJECT_TYPE_SPACEMAN_FREE_QUEUE = 0x00000009
OBJECT_TYPE_EXTENT_LIST_TREE = 0x0000000a
OBJECT_TYPE_OMAP = 0x0000000b
OBJECT_TYPE_CHECKPOINT_MAP = 0x0000000c
OBJECT_TYPE_FS = 0x0000000d
OBJECT_TYPE_FSTREE = 0x0000000e
OBJECT_TYPE_BLOCKREFTREE = 0x0000000f
OBJECT_TYPE_SNAPMETATREE = 0x00000010
OBJECT_TYPE_NX_REAPER = 0x00000011
OBJECT_TYPE_NX_REAP_LIST = 0x00000012
OBJECT_TYPE_OMAP_SNAPSHOT = 0x00000013
OBJECT_TYPE_EFI_JUMPSTART = 0x00000014
OBJECT_TYPE_FUSION_MIDDLE_TREE = 0x00000015
OBJECT_TYPE_NX_FUSION_WBC = 0x00000016
OBJECT_TYPE_NX_FUSION_WBC_LIST = 0x00000017
OBJECT_TYPE_ER_STATE = 0x00000018
OBJECT_TYPE_GBITMAP = 0x00000019
OBJECT_TYPE_GBITMAP_TREE = 0x0000001a
OBJECT_TYPE_GBITMAP_BLOCK = 0x0000001b
OBJECT_TYPE_ER_RECOVERY_BLOCK = 0x0000001c
OBJECT_TYPE_SNAP_META_EXT = 0x0000001d
OBJECT_TYPE_INTEGRITY_META = 0x0000001e
OBJECT_TYPE_FEXT_TREE = 0x0000001f
OBJECT_TYPE_RESERVED_20 = 0x00000020
OBJECT_TYPE_INVALID = 0x00000000
OBJECT_TYPE_TEST = 0x000000ff

# Object Type Flags

OBJ_VIRTUAL = 0x00000000
OBJ_EPHEMERAL = 0x80000000
OBJ_PHYSICAL = 0x40000000
OBJ_NOHEADER = 0x20000000
OBJ_ENCRYPTED = 0x10000000
OBJ_NONPERSISTENT = 0x08000000

MAX_CKSUM_SIZE = 8

BTNODE_ROOT = 0x0001
BTNODE_LEAF = 0x0002
BTNODE_FIXED_KV_SIZE = 0x0004
BTNODE_HASHED = 0x0008
BTNODE_NOHEADER = 0x0010
BTNODE_CHECK_KOFF_INVAL = 0x8000

APFS_MODIFIED_NAMELEN = 32

APFS_MAGIC = 'BSPA'
APFS_MAX_HIST = 8
APFS_VOLNAME_LEN = 256

ObjPhys = Struct(
	o_chksum=Bytes(MAX_CKSUM_SIZE),
	o_oid=OID,
	o_xid=XID,
	o_type=Int32ul,
	o_subtype=Int32ul,
)

CheckpointMapping = Struct(
	cpm_type=Int32ul,
	cpm_subtype=Int32ul,
	cpm_size=Int32ul,
	cpm_pad=Int32ul,
	cpm_fs_oid=OID,
	cpm_oid=OID,
	cpm_paddr=OID,
)

CheckpointMapPhys = Struct(
	cpm_o=ObjPhys,
	cpm_flags=Int32ul,
	cpm_count=Int32ul,
	cpm_map=Array(this.cpm_count, CheckpointMapping),
)

NX_MAX_FILE_SYSTEMS = 100
NX_NUM_COUNTERS = 32
NX_EPH_INFO_COUNT = 4
NX_MAGIC = b'NXSB'

NXSuperBlock = Struct(
	nx_o=ObjPhys,
	nx_magic=Const(NX_MAGIC),
	nx_block_size=Int32ul,
	nx_block_count=Int64ul,
	nx_features=Int64ul,
	nx_readonly_compatible_features=Int64ul,
	nx_incompatible_features=Int64ul,
	uuid=UUID,
	nx_next_oid=OID,
	nx_next_xid=XID,
	nx_xp_desc_blocks=Int32ul,
	nx_xp_data_blocks=Int32ul,
	nx_xp_desc_base=PAddr,
	nx_xp_data_base=PAddr,
	nx_xp_desc_next=Int32ul,
	nx_xp_data_next=Int32ul,
	nx_xp_desc_index=Int32ul,
	nx_xp_desc_len=Int32ul,
	nx_xp_data_index=Int32ul,
	nx_xp_data_len=Int32ul,
	nx_spaceman_oid=OID,
	nx_omap_oid=OID,
	nx_reaper_oid=OID,
	nx_test_type=Int32ul,
	nx_max_file_systems=Int32ul,
	nx_fs_oid=Array(NX_MAX_FILE_SYSTEMS, OID),
	nx_counters=Array(NX_NUM_COUNTERS, Int64ul),
	nx_blocked_out_prange=PRange,
	nx_evict_mapping_tree_oid=OID,
	nx_flags=Int64ul,
	nx_efi_jumpstart=PAddr,
	nx_fusion_uuid=UUID,
	nx_keylocker=PRange,
	nx_ephemeral_info=Array(NX_EPH_INFO_COUNT, Int64ul),
	nx_test_oid=OID,
	nx_fusion_mt_oid=OID,
	nx_fusion_wbc_oid=OID,
	nx_fusion_wbc=PRange,
	nx_newest_mounted_version=Int64ul,
	nx_mkb_locker=PRange,
)

OMapPhys = Struct(
	om_o=ObjPhys,
	om_flags=Int32ul,
	om_snap_count=Int32ul,
	om_tree_type=Int32ul,
	om_snapshot_tree_type=Int32ul,
	om_tree_oid=OID,
	om_snapshot_tree_oid=OID,
	om_most_recent_snap=XID,
	om_pending_revert_min=XID,
	om_pending_revert_max=XID
)

OMapKey = Struct(
	ok_oid=OID,
	ok_xid=XID,
)

OMapVal = Struct(
	ov_flags=Int32ul,
	ov_size=Int32ul,
	ov_paddr=PAddr,
)

NLoc = Struct(
	offset=Int16ul,
	len=Int16ul
)

BtreeNodePhys = Struct(
	btn_o=ObjPhys,
	btn_flags=Int16ul,
	btn_level=Int16ul,
	btn_nkeys=Int32ul,
	btn_table_space=NLoc,
	btn_free_space=NLoc,
	btn_key_free_list=NLoc,
	btn_val_free_list=NLoc
)

KVOff = Struct(
	k=Int16ul,
	v=Int16ul,
)

KVLoc = Struct(
	k=NLoc,
	v=NLoc,
)

BTreeInfoFixed = Struct(
	bt_flags=Int32ul,
	bt_node_size=Int32ul,
	bt_key_size=Int32ul,
	bt_val_size=Int32ul,
)

BTreeInfo = Struct(
	bt_fixed=BTreeInfoFixed,
	bt_longest_key=Int32ul,
	bt_longest_val=Int32ul,
	bt_key_count=Int64ul,
	bt_node_count=Int64ul,
)

CpKeyClass = Int32ul
CpKeyOsVersion = Int32ul
CpKeyRevision = Int16ul
CryptoFlags = Int32ul

WrappedMetaCryptoState = Struct(
	major_version=Int16ul,
	minor_version=Int16ul,
	cpflags=CryptoFlags,
	persistent_class=CpKeyClass,
	key_os_version=CpKeyOsVersion,
	key_revision=CpKeyRevision,
	unused=Int16ul
)

ApfsModifiedBy = Struct(
	id=PaddedString(APFS_MODIFIED_NAMELEN, 'utf8'),
	timestamp=Int64ul,
	last_xid=XID,
)

ApfsSuperBlock = Struct(
	apfs_o=ObjPhys,
	apfs_magic=Int32ul,
	apfs_fs_index=Int32ul,
	apfs_features=Int64ul,
	apfs_readonly_compatible_features=Int64ul,
	apfs_incompatible_features=Int64ul,
	apfs_unmount_time=Int64ul,
	apfs_fs_reserve_block_count=Int64ul,
	apfs_fs_quota_block_count=Int64ul,
	apfs_fs_alloc_count=Int64ul,
	apfs_meta_crypto=WrappedMetaCryptoState,
	apfs_root_tree_type=Int32ul,
	apfs_extentref_tree_type=Int32ul,
	apfs_snap_meta_tree_type=Int32ul,
	apfs_omap_oid=OID,
	apfs_root_tree_oid=OID,
	apfs_extentref_tree_oid=OID,
	apfs_snap_meta_tree_oid=OID,
	apfs_revert_to_xid=XID,
	apfs_revert_to_sblock_oid=OID,
	apfs_next_obj_id=Int64ul,
	apfs_num_files=Int64ul,
	apfs_num_directories=Int64ul,
	apfs_num_symlinks=Int64ul,
	apfs_num_other_fsobjects=Int64ul,
	apfs_num_snapshots=Int64ul,
	apfs_total_blocks_alloced=Int64ul,
	apfs_total_blocks_freed=Int64ul,
	apfs_vol_uuid=UUID,
	apfs_last_mod_time=Int64ul,
	apfs_fs_flags=Int64ul,
	apfs_formatted_by=ApfsModifiedBy,
	apfs_modified_by=Array(APFS_MAX_HIST, ApfsModifiedBy),
	apfs_volname=PaddedString(APFS_VOLNAME_LEN, "utf8"),
	apfs_next_doc_id=Int32ul,
	apfs_role=Int16ul,
	reserved=Int16ul,
	apfs_root_to_xid=XID,
	apfs_er_state_oid=OID,
	apfs_cloneinfo_id_epoch=Int64ul,
	apfs_cloneinfo_xid=Int64ul,
	apfs_snap_meta_ext_oid=OID,
	apfs_volume_group_id=UUID,
	apfs_integrity_meta_oid=OID,
	apfs_fext_tree_oid=OID,
	apfs_fext_tree_type=Int32ul,
	reserved_type=Int32ul,
	reserved_oid=OID,
)

@contextmanager
def file_keep_pos(f):
	start_pos = f.tell()
	try:
		yield
	finally:
		f.seek(start_pos, os.SEEK_SET)


def read_btree_fixed_size(f, block_size: int, btree_pos, k: Construct, v: Construct) -> list[
	tuple[Container, Container]]:
	with file_keep_pos(f):
		f.seek(btree_pos, os.SEEK_SET)
		btree = BtreeNodePhys.parse_stream(f)
		btree_btn_data_pos = f.tell()

		if not (btree.btn_flags & BTNODE_FIXED_KV_SIZE):
			raise RuntimeError("Didnt expect none BTNODE_FIXED_KV_SIZE")

		if not (btree.btn_flags & BTNODE_ROOT):
			raise RuntimeError("Didnt expect none BTNODE_ROOT")

		if not (btree.btn_flags & BTNODE_LEAF):
			raise RuntimeError("Didnt expect none BTNODE_LEAF")

		f.seek(btree_pos + block_size - BTreeInfo.sizeof(), os.SEEK_SET)
		btree_info = BTreeInfo.parse_stream(f)

		if k.sizeof() != btree_info.bt_fixed.bt_key_size:
			raise RuntimeError(f"{btree_info.bt_fixed.bt_key_size=} while expecting {k.sizeof()=}")

		if v.sizeof() != btree_info.bt_fixed.bt_val_size:
			raise RuntimeError(f"{btree_info.bt_fixed.bt_val_size=} while expecting {v.sizeof()=}")

		KVOffArray = Array(btree.btn_nkeys, KVOff)

		f.seek(btree_btn_data_pos + btree.btn_table_space.offset, os.SEEK_SET)
		kvoffs = KVOffArray.parse_stream(f)

		keys_base_pos = btree_btn_data_pos + btree.btn_table_space.offset + btree.btn_table_space.len
		values_base_pos = btree_pos + block_size - BTreeInfo.sizeof()

		key_vals = []

		for kvoff in kvoffs:
			f.seek(keys_base_pos + kvoff.k, os.SEEK_SET)
			key = k.parse_stream(f)

			f.seek(values_base_pos - kvoff.v, os.SEEK_SET)
			val = v.parse_stream(f)

			key_vals.append((key, val))

		return key_vals


def extract_files(path: Path, out_dir: Path) -> list[Path]:
	out_dir.mkdir(parents=True, exist_ok=True)

	with (path.open('rb') as f):
		nx_superblock = NXSuperBlock.parse_stream(f)
		block_size = nx_superblock.nx_block_size

		f.seek(nx_superblock.nx_omap_oid * block_size, os.SEEK_SET)
		nx_omap_phys = OMapPhys.parse_stream(f)

		omap_list = read_btree_fixed_size(f, block_size, nx_omap_phys.om_tree_oid * block_size, OMapKey, OMapVal)

		fs_oids = [oid for oid in nx_superblock.nx_fs_oid if oid != 0]

		for fs_oid in fs_oids:
			relevant_omap_kvs = [omap_kv for omap_kv in omap_list if omap_kv[0].ok_oid == fs_oid]
			top_xid_omap_entry = max(relevant_omap_kvs, key=lambda omap_kv: omap_kv[0].ok_xid)

			f.seek(top_xid_omap_entry[1].ov_paddr * block_size, os.SEEK_SET)
			apfs_superblock = ApfsSuperBlock.parse_stream(f)

	return []
