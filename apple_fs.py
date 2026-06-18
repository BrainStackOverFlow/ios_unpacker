# Based on:
# https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf
import os
from contextlib import contextmanager
from pathlib import Path

from construct import Struct, Bytes, Int64ul, Int32ul, Array, this, Const, Int16ul, Construct, Container, PaddedString, \
	Computed, Switch, Tell, IfThenElse, Int8ul

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

OBJ_STORAGETYPE_MASK = 0xc0000000

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

BTOFF_INVALID = 0xFFFF

BTREE_UINT64_KEYS = 0x00000001
BTREE_SEQUENTIAL_INSERT = 0x00000002
BTREE_ALLOW_GHOSTS = 0x00000004
BTREE_EPHEMERAL = 0x00000008
BTREE_PHYSICAL = 0x00000010
BTREE_NONPERSISTENT = 0x00000020
BTREE_KV_NONALIGNED = 0x00000040
BTREE_HASHED = 0x00000080
BTREE_NOHEADER = 0x00000100

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

BTREE_NODE_HASH_SIZE_MAX = 64

BtnIndexNodeVal = Struct(
	binv_child_oid=OID,
	binv_child_hash=Bytes(BTREE_NODE_HASH_SIZE_MAX),
)

OBJ_ID_MASK = 0x0fffffffffffffff
OBJ_TYPE_MASK = 0xf000000000000000
OBJ_TYPE_SHIFT = 60
SYSTEM_OBJ_ID_MARK = 0x0fffffff00000000

JKey = Struct(
	obj_id_and_type=Int64ul,
	obj_id=Computed(this.obj_id_and_type & OBJ_ID_MASK),
	obj_type=Computed((this.obj_id_and_type & OBJ_TYPE_MASK) >> OBJ_TYPE_SHIFT),
)

APFS_TYPE_ANY = 0
APFS_TYPE_SNAP_METADATA = 1
APFS_TYPE_EXTENT = 2
APFS_TYPE_INODE = 3
APFS_TYPE_XATTR = 4
APFS_TYPE_SIBLING_LINK = 5
APFS_TYPE_DSTREAM_ID = 6
APFS_TYPE_CRYPTO_STATE = 7
APFS_TYPE_FILE_EXTENT = 8
APFS_TYPE_DIR_REC = 9
APFS_TYPE_DIR_STATS = 10
APFS_TYPE_SNAP_NAME = 11
APFS_TYPE_SIBLING_MAP = 12
APFS_TYPE_FILE_INFO = 13
APFS_TYPE_MAX_VALID = 13
APFS_TYPE_MAX = 15
APFS_TYPE_INVALID = 15

EmptyKeyRest = Struct()

JNameKeyRest = Struct(
	name_len=Int16ul,
	name=PaddedString(this.name_len, 'utf-8'),
)

J_DREC_LEN_MASK = 0x000003ff
J_DREC_HASH_MASK = 0xfffff400
J_DREC_HASH_SHIFT = 10

JDRecHashedKeyRest = Struct(
	name_len_and_hash=Int32ul,
	name_len=Computed(this.name_len_and_hash & J_DREC_LEN_MASK),
	name_hash=Computed((this.name_len_and_hash & J_DREC_HASH_MASK) >> J_DREC_HASH_SHIFT),
	name=PaddedString(this.name_len, 'utf-8'),
)

JXattrKeyRest = Struct(
	name_len=Int16ul,
	name=PaddedString(this.name_len, 'utf-8'),
)

JDRecKeyRest = Struct(
	name_len=Int16ul,
	name=PaddedString(this.name_len, 'utf-8'),
)

JFileExtentKeyRest = Struct(
	logical_addr=Int64ul,
)

APFSRootTreeKey = Struct(
	hdr=JKey,
	body=Switch(this.hdr.obj_type, {
		APFS_TYPE_INODE: EmptyKeyRest,
		APFS_TYPE_XATTR: JXattrKeyRest,
		APFS_TYPE_DIR_REC: JDRecHashedKeyRest,
	}, default=Bytes(this._params.k_len - JKey.sizeof())),
)

XField = Struct(
	x_type=Int8ul,
	x_flags=Int8ul,
	x_size=Int16ul,
)

XFBlob = Struct(
	xf_num_exts=Int16ul,
	xf_used_data=Int16ul,
)

INO_EXT_TYPE_DELTA_TREE_OID = 2
INO_EXT_TYPE_DOCUMENT_ID = 3
INO_EXT_TYPE_NAME = 4
INO_EXT_TYPE_PREV_FSIZE = 5
INO_EXT_TYPE_RESERVED_6 = 6
INO_EXT_TYPE_FINDER_INFO = 7
INO_EXT_TYPE_DSTREAM = 8
INO_EXT_TYPE_RESERVED_9 = 9
INO_EXT_TYPE_DIR_STATS_KEY = 10
INO_EXT_TYPE_FS_UUID = 11
INO_EXT_TYPE_RESERVED_12 = 12
INO_EXT_TYPE_SPARSE_BYTES = 13
INO_EXT_TYPE_RDEV = 14
INO_EXT_TYPE_PURGEABLE_FLAGS = 15
INO_EXT_TYPE_ORIG_SYNC_ROOT_ID = 16


def align_up_to_8(n):
	return (n + 7) & ~7


XFields = Struct(
	xf_blob=XFBlob,
	xfields_meta=Array(this.xf_blob.xf_num_exts, XField),
	xfields_raw=Array(
		this.xf_blob.xf_num_exts,
		Struct(
			_size=Computed(lambda ctx: ctx._.xfields_meta[ctx._index].x_size),
			data=Bytes(lambda ctx: ctx._size),
			padding=Bytes(lambda ctx: align_up_to_8(ctx._size) - ctx._size),
		),
	),
	xfields=Array(
		this.xf_blob.xf_num_exts,
		Struct(
			_raw=Computed(lambda ctx: ctx._.xfields_raw[ctx._index].data),
			type=Computed(lambda ctx: ctx._.xfields_meta[ctx._index].x_type),
			value=Switch(this.type, {
				INO_EXT_TYPE_NAME: Computed(lambda ctx: ctx._raw.decode("utf-8")),
			}, default=Computed(this._raw)),
		),
	),
)

UID = Int32ul
GID = Int32ul
Mode = Int16ul
CPKeyClass = Int32ul

JINodeVal = Struct(
	_fixed_start=Tell,
	parent_id=Int64ul,
	private_id=Int64ul,
	create_time=Int64ul,
	mod_time=Int64ul,
	change_time=Int64ul,
	access_time=Int64ul,
	internal_flags=Int64ul,
	nchildren_nlink=Int32ul,
	nchildren=Computed(this.nchildren_nlink),
	nlink=Computed(this.nchildren_nlink),
	default_protection_class=CPKeyClass,
	write_generation_counter=Int32ul,
	bsd_flags=Int32ul,
	owner=UID,
	group=GID,
	mode=Mode,
	pad1=Int16ul,
	uncompressed_size=Int64ul,
	_fixed_end=Tell,
	_fixed_size=Computed(this._fixed_end - this._fixed_start),
	_xfields_size=Computed(this._params.v_len - this._fixed_size),
	_xfields_bytes=Bytes(this._xfields_size),
	xfields=IfThenElse(
		lambda ctx: ctx._xfields_size > 0,
		Computed(lambda ctx: XFields.parse(ctx._xfields_bytes)),
		Computed(lambda ctx: None),
	),
)

JXattrVal = Struct(
	flags=Int16ul,
	xdata_len=Int16ul,
	xdata=Bytes(this.xdata_len),
)

JDRecVal = Struct(
	_fixed_start=Tell,
	file_id=Int64ul,
	date_added=Int64ul,
	flags=Int16ul,
	_fixed_end=Tell,
	_fixed_size=Computed(this._fixed_end - this._fixed_start),
	_xfields_size=Computed(this._params.v_len - this._fixed_size),
	_xfields_bytes=Bytes(this._xfields_size),
	xfields=IfThenElse(
		lambda ctx: ctx._xfields_size > 0,
		Computed(lambda ctx: XFields.parse(ctx._xfields_bytes)),
		Computed(lambda ctx: None),
	),
)

APFSRootTreeValue = Struct(
	body=Switch(this._params.key_obj.hdr.obj_type, {
		APFS_TYPE_INODE: JINodeVal,
		APFS_TYPE_XATTR: JXattrVal,
		APFS_TYPE_DIR_REC: JDRecVal,
	}, default=Bytes(this._params.v_len)),
)

J_FILE_EXTENT_LEN_MASK = 0x00ffffffffffffff
J_FILE_EXTENT_FLAG_MASK = 0xff00000000000000
J_FILE_EXTENT_FLAG_SHIFT = 56

FExtTreeKey = Struct(
	private_id=Int64ul,
	logical_addr=Int64ul,
)

FExtTreeVal = Struct(
	len_and_flags=Int64ul,
	phys_block_num=Int64ul,
	len=Computed(this.len_and_flags & J_FILE_EXTENT_LEN_MASK),
	flags=Computed((this.len_and_flags & J_FILE_EXTENT_FLAG_MASK) >> J_FILE_EXTENT_FLAG_SHIFT),
)


@contextmanager
def file_keep_pos(f):
	start_pos = f.tell()
	try:
		yield
	finally:
		f.seek(start_pos, os.SEEK_SET)


def read_btree_node(
		f,
		block_size: int,
		node_pos: int,
		btree_info,
		k: Construct,
		v: Construct,
		omap_list: list | None,
		btree_root_oid,
) -> list[tuple[Container, Container]]:
	f.seek(node_pos, os.SEEK_SET)
	node = BtreeNodePhys.parse_stream(f)
	btn_data_pos = f.tell()

	# print(
	# 	"NODE",
	# 	"pos", hex(node_pos),
	# 	"level", node.btn_level,
	# 	"nkeys", node.btn_nkeys,
	# 	"flags", hex(node.btn_flags),
	# )

	is_root = bool(node.btn_flags & BTNODE_ROOT)
	is_leaf = bool(node.btn_flags & BTNODE_LEAF)
	is_fixed = bool(node.btn_flags & BTNODE_FIXED_KV_SIZE)
	is_hashed = bool(node.btn_flags & BTNODE_HASHED)

	is_physical_btree = bool(btree_info.bt_fixed.bt_flags & BTREE_PHYSICAL)
	is_ephemeral_btree = bool(btree_info.bt_fixed.bt_flags & BTREE_EPHEMERAL)

	node_size = btree_info.bt_fixed.bt_node_size
	key_size = btree_info.bt_fixed.bt_key_size
	leaf_value_size = btree_info.bt_fixed.bt_val_size

	if is_fixed and key_size == 0:
		raise ValueError(
			f"node at 0x{node_pos:x} is fixed-size but bt_key_size is 0"
		)

	if is_fixed and leaf_value_size == 0:
		raise ValueError(
			f"leaf node at 0x{node_pos:x} is fixed-size but bt_val_size is 0"
		)

	toc_pos = btn_data_pos + node.btn_table_space.offset
	key_area_pos = toc_pos + node.btn_table_space.len

	value_area_end = node_pos + node_size
	if is_root:
		value_area_end -= BTreeInfo.sizeof()

	toc_entry_size = KVOff.sizeof() if is_fixed else KVLoc.sizeof()

	pairs = []

	for i in range(node.btn_nkeys):
		toc_entry_pos = toc_pos + i * toc_entry_size

		if is_fixed:
			f.seek(toc_entry_pos, os.SEEK_SET)
			entry = KVOff.parse_stream(f)

			k_off = entry.k
			k_len = key_size
			v_off = entry.v
			v_len = leaf_value_size
		else:
			f.seek(toc_entry_pos, os.SEEK_SET)
			entry = KVLoc.parse_stream(f)

			k_off = entry.k.offset
			k_len = entry.k.len
			v_off = entry.v.offset
			v_len = entry.v.len

		if v_off == BTOFF_INVALID:
			continue

		key_pos = key_area_pos + k_off
		value_pos = value_area_end - v_off

		if is_leaf:
			f.seek(key_pos, os.SEEK_SET)
			key_obj = k.parse_stream(f, k_len=k_len)

			f.seek(value_pos, os.SEEK_SET)
			value_obj = v.parse_stream(f, v_len=v_len, key_obj=key_obj)

			pairs.append((key_obj, value_obj))
		else:
			f.seek(value_pos, os.SEEK_SET)

			if is_hashed:
				btn_index_node_val = BtnIndexNodeVal.parse_stream(f)
				oid = btn_index_node_val.binv_child_oid + btree_root_oid
			else:
				oid = OID.parse_stream(f)

			if is_physical_btree:
				child_pos = oid * block_size
			elif is_ephemeral_btree:
				raise NotImplementedError(f"ephemeral btree child oid {oid}")
			else:
				if omap_list is None:
					raise ValueError(f"virtual btree child oid {oid} but no omap_list")

				child_omap_val = latest_omap_val(omap_list, oid)
				child_pos = child_omap_val.ov_paddr * block_size

			pairs.extend(
				read_btree_node(
					f=f,
					block_size=block_size,
					node_pos=child_pos,
					btree_info=btree_info,
					k=k,
					v=v,
					omap_list=omap_list,
					btree_root_oid=btree_root_oid,
				)
			)

	return pairs


def read_btree(
		f,
		block_size: int,
		btree_pos: int,
		k: Construct,
		v: Construct,
		omap_list: list | None,
		root_btree_oid,
) -> list[tuple[Container, Container]]:
	with file_keep_pos(f):
		f.seek(btree_pos, os.SEEK_SET)
		root = BtreeNodePhys.parse_stream(f)

		if not (root.btn_flags & BTNODE_ROOT):
			raise ValueError(f"node at 0x{btree_pos:x} is not a root node")

		f.seek(btree_pos + block_size - BTreeInfo.sizeof(), os.SEEK_SET)
		btree_info = BTreeInfo.parse_stream(f)

		if root_btree_oid is None:
			root_btree_oid = root.btn_o.o_oid

		return read_btree_node(
			f=f,
			block_size=block_size,
			node_pos=btree_pos,
			btree_info=btree_info,
			k=k,
			v=v,
			omap_list=omap_list,
			btree_root_oid=root_btree_oid,
		)


def latest_omap_val(omap_list: list[tuple[Container, Container]], oid: int) -> Container:
	relevant_omap_kvs = [omap_kv for omap_kv in omap_list if omap_kv[0].ok_oid == oid]

	if not relevant_omap_kvs:
		raise ValueError(f"could not find oid {oid} in omap")

	return max(relevant_omap_kvs, key=lambda omap_kv: omap_kv[0].ok_xid)[1]


def extract_files(path: Path, out_dir: Path) -> list[Path]:
	out_dir.mkdir(parents=True, exist_ok=True)

	with (path.open('rb') as f):
		nx_superblock = NXSuperBlock.parse_stream(f)
		block_size = nx_superblock.nx_block_size

		f.seek(nx_superblock.nx_omap_oid * block_size, os.SEEK_SET)
		nx_omap_phys = OMapPhys.parse_stream(f)

		omap_list = read_btree(f, block_size, nx_omap_phys.om_tree_oid * block_size, OMapKey, OMapVal, None, None)

		fs_oids = [oid for oid in nx_superblock.nx_fs_oid if oid != 0]

		for fs_oid in fs_oids:
			fs_omap_entry = latest_omap_val(omap_list, fs_oid)
			f.seek(fs_omap_entry.ov_paddr * block_size, os.SEEK_SET)
			apfs_superblock = ApfsSuperBlock.parse_stream(f)

			f.seek(apfs_superblock.apfs_omap_oid * block_size, os.SEEK_SET)
			apfs_omap = OMapPhys.parse_stream(f)
			apfs_omap_list = read_btree(f, block_size, apfs_omap.om_tree_oid * block_size, OMapKey, OMapVal, None, None)

			root_tree_omap_entry = latest_omap_val(apfs_omap_list, apfs_superblock.apfs_root_tree_oid)
			root_tree_addr = root_tree_omap_entry.ov_paddr * block_size
			root_fs_entries = read_btree(
				f,
				block_size,
				root_tree_addr,
				APFSRootTreeKey,
				APFSRootTreeValue,
				apfs_omap_list,
				apfs_superblock.apfs_root_tree_oid,
			)

			fext_fs_entries = []
			fext_tree_oid = apfs_superblock.apfs_fext_tree_oid
			if fext_tree_oid != 0:
				fext_tree_storage = apfs_superblock.apfs_fext_tree_type & OBJ_STORAGETYPE_MASK

				if fext_tree_storage == OBJ_PHYSICAL:
					fext_tree_addr = fext_tree_oid * block_size
				elif fext_tree_storage == OBJ_VIRTUAL:
					fext_tree_omap_entry = latest_omap_val(apfs_omap_list, fext_tree_oid)
					fext_tree_addr = fext_tree_omap_entry.ov_paddr * block_size
				else:
					raise RuntimeError(f"unknown fext tree storage type {fext_tree_oid}")

				fext_fs_entries = read_btree(f, block_size, fext_tree_addr, FExtTreeKey, FExtTreeVal, apfs_omap_list,
				                             fext_tree_oid)

			volume_name = apfs_superblock.apfs_volname
			out_volume_name = out_dir / volume_name
			out_volume_name.mkdir(parents=True, exist_ok=True)

			print("A")

			root_fs_entries = []
			fext_fs_entries = []

		return []
