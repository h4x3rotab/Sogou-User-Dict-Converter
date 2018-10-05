import struct

class KeyItem(object):
    datatype_size = [4,1,1,2,1,2,2,4,4,8,4,4,4,0,0,0]

    def __init__(self):
        self.dict_typedef = 0
        self.datatype = []
        self.attr_idx = 0
        self.v4 = 0
        self.v5 = 0
        self.v6 = 0        

class HeaderItem(object):
    def __init__(self):
        self.offset = 0
        self.datasize = 0
        self.used_datasize = 0

class AttributeItem(object):
    def __init__(self):
        self.count = 0
        self.a2 = 0
        self.data_id = 0
        self.b2 = 0

class HashStore(object):
    def __init__(self):
        self.offset = 0
        self.count = 0

    def parse(self, f):
        self.offset = readUint32(f)
        self.count = readUint32(f)

''' Dict Structure
key -> attrId        attr_store[data]
        -> dataId  ds[data]
    -> keyDataId   ds[data]
    -> dataId      ds[data]
'''

class BaseDict(object):
    datatype_hash_size = [0, 27, 414, 512, -1, -1, 512, 0]

    def __init__(self, corev3=True):
        self.attr = None
        self.key = None
        self.aint = None
        self.header_index = None
        self.header_attr = None
        self.datastore = None
        self.ds_base = None
        self.datatype_size = None
        self.attr_size = None
        self.base_hash_size = None
        self.key_hash_size = [0]*10
        self.aflag = False
        if corev3:  # t_usrDictV3Core::t_usrDictV3Core
            self.key_hash_size[0] = 500

    def init(self):
        self.datatype_size = []
        self.base_hash_size = []
        self.attr_size = [0] * len(self.attr)
        for idx_key, key in enumerate(self.key):
            size = (key.dict_typedef >> 2) & 4
            masked_typedef = key.dict_typedef & 0xFFFFFF8F
            # hash item
            if self.key_hash_size[idx_key] > 0:
                self.base_hash_size.append(self.key_hash_size[idx_key])
            else:
                self.base_hash_size.append(BaseDict.datatype_hash_size[masked_typedef])
            # datatype size
            if key.attr_idx < 0:
                for i, datatype in enumerate(key.datatype):
                    if i > 0 or masked_typedef != 4:
                        size += KeyItem.datatype_size[datatype]
                if key.attr_idx == -1:
                    size += 4
                self.datatype_size.append(size)
            else:
                num_attr = self.attr[key.attr_idx].count
                # non-attr data size
                num_non_attr = len(key.datatype) - num_attr
                for i in range(num_non_attr):
                    if i > 0 or masked_typedef != 4:
                        size += KeyItem.datatype_size[key.datatype[i]]
                if key.dict_typedef & 0x60 > 0:
                    size += 4
                size += 4
                self.datatype_size.append(size)
                # attr data size
                attr_size = 0
                for i in range(num_non_attr, len(key.datatype)):
                    attr_size += KeyItem.datatype_size[key.datatype[i]]
                if (key.dict_typedef & 0x40) == 0:
                    attr_size += 4
                self.attr_size[key.attr_idx] = attr_size
                # ???
                if self.attr[key.attr_idx].b2 == 0:
                    self.aflag = True

    def GetHashStore(self, index_id, datatype):
        if index_id < 0 or datatype > 6 or index_id > len(self.header_index):
            assert False
        index_offset = self.header_index[index_id].offset
        assert index_offset >= 0
        size = self.base_hash_size[index_id]
        offset = index_offset - 8 * size
        assert offset >= 0
        return self.ds_base.subview(offset)

    def GetIndexStore(self, index_id):
        return self.ds_base.subview(self.header_index[index_id].offset)

    def GetAttriStore(self, attr_id):
        return self.ds_base.subview(self.header_attr[attr_id].offset)

    def GetAttriFromIndex(self, index_id, attr_id, offset):
        datatype_size = self.datatype_size[index_id]
        data_offset = offset + datatype_size * attr_id
        return self.GetIndexStore(index_id).subview(data_offset)

    def GetAttriFromAttri(self, key_id, offset):
        attr_id = self.key[key_id].attr_idx
        attri_store = self.GetAttriStore(attr_id).subview(offset)
        if attri_store.pos >= len(attri_store.buff):
            return None
        return attri_store

    def GetAllDataWithAttri(self, key_id):
        results = []
        key = self.key[key_id]
        hashstore_base = self.GetHashStore(key_id, key.dict_typedef & 0xFFFFFF8F)
        attr_header = self.header_attr[key.attr_idx]
        if attr_header.used_datasize == 0:
            num_attr = attr_header.data_size
        else:
            num_attr = attr_header.used_datasize
        num_hashstore = self.base_hash_size[key_id]
        print(f'base_hash_size: {num_hashstore} num_attr: {num_attr}')
        for idx_hashstore in range(num_hashstore):
            hashstore = HashStore()
            hashstore.parse(hashstore_base)
            print(f'hashstore [ offset: {hashstore.offset}, count: {hashstore.count} ]')
            for attr_id in range(hashstore.count):
                attr_base = self.GetAttriFromIndex(key_id, attr_id, hashstore.offset)
                offset = readUint32(attr_base.subview(self.datatype_size[key_id] - 4))
                print(f'attr_id: {attr_id} offset: {offset}')
                # input()
                for attr2_id in range(num_attr):
                    attr2_base = self.GetAttriFromAttri(key_id, offset)
                    if attr2_base is None:
                        print(f'attr2 out of range (offset: {offset})')
                        break
                    results.append((attr_base, attr2_base))
                    offset = readInt32(attr2_base.subview(self.attr_size[key.attr_idx] - 4))
                    print(f'attr2_id: {attr2_id} new offset: {offset}')
                    if offset == -1:
                        break
        return results
            

class DataView(object):
    def __init__(self, buff, pos=0):
        self.buff = buff
        self.pos = pos

    def read(self, n):
        assert n >= 0
        end = self.pos + n
        assert end <= len(self.buff)
        data = self.buff[self.pos : end]
        self.pos = end
        return data

    def len(self):
        return len(self.buff) - self.pos

    def subview(self, off=0):
        return DataView(self.buff, self.pos + off)

def readInt32(b):
    return struct.unpack('<i', b.read(4))[0]

def readUint32(b):
    return struct.unpack('<I', b.read(4))[0]

def readUint16(b):
    return struct.unpack('<H', b.read(2))[0]

filedata = open('dict.bin', 'rb').read()
size = len(filedata)
f = DataView(filedata)

file_chksum = readUint32(f)
uint_4 = readUint32(f)
uint_8 = readUint32(f)
uint_12 = readUint32(f)
uint_16 = readUint32(f)

print('uint0-16:', file_chksum, uint_4, uint_8, uint_12, uint_16)
config_size = uint_4
chksum = uint_4 + uint_8 + uint_12 + uint_16

assert 0 <= uint_4 <= size

f2 = DataView(filedata, uint_4 + 8)
f_s8 = DataView(filedata, 20)
pos_2 = uint_4 + 8

key_items = []
if uint_8 > 0:
    # parse section 8
    for i in range(uint_8):
        key = KeyItem()
        key.dict_typedef = readUint16(f_s8)
        assert key.dict_typedef < 100
        num_datatype = readUint16(f_s8)
        if num_datatype > 0:
            for _ in range(num_datatype):
                datatype = readUint16(f_s8)
                key.datatype.append(datatype)
        key.attr_idx = readUint32(f_s8)
        key.v4 = readUint32(f_s8)
        key.v5 = readUint32(f_s8)
        key.v6 = readUint32(f_s8)
        key_items.append(key)

attr_items = []
if uint_12 > 0:
    for _ in range(uint_12):
        attr = AttributeItem()
        attr.count = readUint32(f_s8)
        attr.a2 = readUint32(f_s8)
        attr.data_id = readUint32(f_s8)
        attr.b2 = readUint32(f_s8)
        attr_items.append(attr)

aint_items = []
if uint_16 > 0:
    for _ in range(uint_16):
        aint = readUint32(f_s8)
        aint_items.append(aint)

assert f_s8.pos == f2.pos  # all the sec8 data has been processed

base_dict = BaseDict()
base_dict.key = key_items
base_dict.attr = attr_items
base_dict.aint = aint_items
base_dict.init()

header_size = 12 * (len(base_dict.attr) + len(base_dict.aint) + len(base_dict.key)) + 24

b2_version = readUint32(f2)
b2_format = readUint32(f2)
print(f'version:{b2_version} format:{b2_format}')

total_size = readUint32(f2)
USR_DICT_HEADER_SIZE = 4 + 76
assert total_size > 0 and total_size + header_size + config_size + 8 == size - USR_DICT_HEADER_SIZE # assert buff2.1

size3_b2 = readUint32(f2)
size4_b2 = readUint32(f2)
size5_b2 = readUint32(f2)
#b2_n = size3_b2 + size4_b2 + size5_b2
# assert b2_n * 12 + 24 == some_size
print('header size:', total_size, size3_b2, size4_b2, size5_b2)

header_items_index = []
for _ in range(size3_b2):
    header = HeaderItem()
    header.offset = readUint32(f2)
    header.datasize = readUint32(f2)
    header.used_datasize = readUint32(f2)
    chksum += header.offset + header.datasize + header.used_datasize
    header_items_index.append(header)
base_dict.header_index = header_items_index

header_items_attr = []
for _ in range(size4_b2):
    header = HeaderItem()
    header.offset = readUint32(f2)
    header.datasize = readUint32(f2)
    header.used_datasize = readUint32(f2)
    chksum += header.offset + header.datasize + header.used_datasize
    header_items_attr.append(header)
base_dict.header_attr = header_items_attr

datastore_items = []
for _ in range(size5_b2):
    header = HeaderItem()
    header.offset = readUint32(f2)
    header.datasize = readUint32(f2)
    header.used_datasize = readUint32(f2)
    chksum += header.offset + header.datasize + header.used_datasize
    datastore_items.append(header)
base_dict.datastore = datastore_items

base_dict.ds_base = f2
assert pos_2 + header_size == f2.pos

# for i in range(len(base_dict.key)):
#     pos = base_dict.get_hash_offset(i)
#     item = base_dict.ds_base[pos] 



# base_dict
# base_dict.header = 

