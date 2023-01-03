"""
工具：Json数据压缩工具
简介：本工具实现了使用HPack算法和CJson算法对json数据的压缩与解压，并在上述两种压缩算法的基础上进行了gzip压缩，从而实现更小压缩率的json数据压缩。

算法简介：
CJson算法是将json数据的key和value抽离成Template与Value，并将重复的key去掉，从而实现json数据压缩。
例子：[{"x": 100, "y": 100}, {"x": 200, "y": 200, "height": 3, "width": 4}] 经CJson算法压缩为 {"t": [[0, "x", "y"], [1, "height", "width"]], "v": [[1, 100, 100], [2, 200, 200, 3, 4]]}
HPack算法适用于泛型同构集合，它也是将json数据的key和value抽离成Template与Value，不过由于集合是泛型同构的，所以所有集合的keys都是一样的，因此只需要记录一组keys和所有的values。
例子：[{"a": "A", "b": "B"}, {"a": "C", "b": "D"}, {"a": "E", "b": "F"}] 经HPack算法压缩为 [2, "a", "b", "A", "B", "C", "D", "E", "F"]

使用说明：
使用HPack算法对json数据进行压缩和解压：HPack.pack() HPack.unpack()
使用CJson算法对json数据进行压缩和解压：CJson.pack() CJson.unpack()
使用HPack+gzip对json数据进行压缩和解压：JsonTools.Hpack_pack() JsonTools.Hpack_unpack()
使用CJson+gzip对json数据进行压缩和解压：JsonTools.Cjson_pack() JsonTools.Cjson_unpack()
ps: 统一json数据格式为存储dict的list
"""

import json
from io import BytesIO
import gzip
import codecs

# use Hpack to pack or unpack json data
class HPack:
    """
    input: list of dict
    output: list
    function: use HPack to pack the json data
    """
    def pack(dict_list):
        length = len(dict_list)
        keys = length and list(dict_list[0].keys()) or []
        klen = len(keys)
        res = []
        i = 0
        while i < length:
            dict_i = dict_list[i]
            ki = 0
            while ki < klen:
                res.append(dict_i[keys[ki]])
                ki = ki + 1
            i = i + 1
        return [klen] + keys + res

    """
    input: list
    output: list of dict
    function: use HPack to unpack the json data
    """
    def unpack(hlist):
        length = len(hlist)
        klen = hlist[0]
        res = []
        i = klen + 1
        while i < length:
            dict_i = dict()
            ki = 0
            while ki < klen:
                ki = ki + 1
                dict_i[hlist[ki]] = hlist[i]
                i = i + 1
            res.append(dict_i)
        return res

# node of Trie
class TrieNode:
    def __init__(self):
        self.id = 0                 # id > 0 is the end of key list
        self.child_dict = dict()    # child dict
    
# use Trie to replace the repeated keys
class Trie:
    def __init__(self):
        self.root = TrieNode()

    """
    input: all of key list
    output: None
    function: use all of key list to create Trie
    """
    def addAll(self, key_alllist):
        length = len(key_alllist)
        for i in range(length):
            self.add(key_alllist[i], i+1)
    
    """
    input: key list
    output: None
    function: add key list to Trie
    """
    def add(self, key_list, id):
        p = self.root
        length = len(key_list)
        for i in range(length):
            if p.child_dict.get(key_list[i]) is None:
                new_node = TrieNode()
                if i == length - 1:
                    new_node.id = id
                p.child_dict[key_list[i]] = new_node
                p = new_node
            else:
                p = p.child_dict[key_list[i]]
                if i == length - 1 and p.id == 0:
                    p.id = id

    """
    input: all of key list
    output: all of replaced key list, list of value index
    function: replace all of repeated keys
    """
    def searchAll(self, key_alllist):
        res = []
        val_list = []
        length = len(key_alllist)
        for i in range(length):
            m_list = self.search(key_alllist[i], i+1)
            if m_list is not None:
                if len(m_list) == 1:
                    val_list.append(m_list[0])
                else:
                    res.append(m_list)
                    val_list.append(i+1)
            else:
                val_list.append(None)
        return res, val_list

    """
    input: key list, id of key list
    output: replaced key list
    function: replace the repeated keys
    """
    def search(self, key_list, id):
        length = len(key_list)
        if length == 0:
            return None
        p = self.root
        pre_id = 0
        start = 0
        for i in range(length):
            p = p.child_dict.get(key_list[i])
            if p is None:
                return False
            if p.id > 0 and id != p.id:
                pre_id = p.id
                start = i+1
        return [pre_id] + key_list[start:]

# use CJson to pack or unpack json data
class CJson:
    """
    input: list of dict
    output: dict
    function: use CJson to pack the json data
    """
    def pack(dict_list):
        key_alllist = []
        value_alllist = []
        length = len(dict_list)
        for i in range(length):
            key_alllist.append(list(dict_list[i].keys()))
            value_alllist.append(list(dict_list[i].values()))

        trie = Trie()
        trie.addAll(key_alllist)

        keys_pack, val_list = trie.searchAll(key_alllist)
        values_pack = []
        for i in range(length):
            if val_list[i] is None:
                values_pack.append([])
            else:
                values_pack.append([val_list[i]]+value_alllist[i])
        res = dict()
        res["t"] = keys_pack
        res["v"] = values_pack
        return res

    """
    input: dict
    output: list of dict
    function: use CJson to unpack the json data
    """
    def unpack(cdict):
        keys_pack = cdict["t"]
        values_pack = cdict["v"]
        length = len(values_pack)
        dict_list = []
        for i in range(length):
            value_list = values_pack[i]
            vlen = len(value_list)
            m_dict = dict()
            if vlen != 0:
                index = value_list[0]
                key_list = keys_pack[index-1]
                while key_list[0] != 0:
                    key_list = keys_pack[key_list[0]-1] + key_list[1:]
                for j in range(1, vlen):
                    m_dict[key_list[j]] = value_list[j]
            dict_list.append(m_dict)
        return dict_list

class GZIP_Tools:
    """
    input: raw data
    output: compressed data
    function: use gzip to compress data
    """
    def compress(raw_data):
        buf = BytesIO()
        with gzip.GzipFile(mode="wb", fileobj=buf) as file:
            with codecs.getwriter("utf-8")(file) as writer:
                writer.write(raw_data)
 
        compressed = buf.getvalue()
        return compressed

    """
    input: compressed data
    output: raw data
    function: use gzip to uncompress data
    """
    def uncompress(compressed):
        inbuffer = BytesIO(compressed)
        with gzip.GzipFile(mode="rb", fileobj=inbuffer) as file:
            raw_data = file.read()
        return raw_data

class JsonZip:
    """
    input: list of dict
    output: binary data
    function: use HPack+gzip to pack the json data
    """
    def Hpack_pack(dict_list):
        hlist = HPack.pack(dict_list)
        s = json.dumps(hlist, separators=(',', ':'))    # remove the space from string
        compressed = GZIP_Tools.compress(s)
        return compressed

    """
    input: binary data
    output: list of dict
    function: use HPack+gzip to unpack the json data
    """
    def Hpack_unpack(compressed):
        raw_data = GZIP_Tools.uncompress(compressed)
        hlist = json.loads(raw_data)
        dict_list = HPack.unpack(hlist)
        return dict_list

    """
    input: list of dict
    output: binary data
    function: use CJson+gzip to pack the json data
    """
    def Cjson_pack(dict_list):
        cdict = CJson.pack(dict_list)
        s = json.dumps(cdict, separators=(',', ':'))    # remove the space from string
        compressed = GZIP_Tools.compress(s)
        return compressed
    
    """
    input: binary data
    output: list of dict
    function: use CJson+gzip to unpack the json data
    """
    def Cjson_unpack(compressed):
        raw_data = GZIP_Tools.uncompress(compressed)
        cdict = json.loads(raw_data)
        dict_list = CJson.unpack(cdict)
        return dict_list

if __name__ == '__main__':
    print('测试样例1')
    print('-' * 100)
    json_data1 = '[{"a": "A", "b": "B", "c": "C"}, {"a": "D", "b": "E", "c": "F"}, {"a": "G", "b": "H", "c": "I"}]'
    print('原始数据: ', json_data1, '长度: ', len(json_data1))

    print('-' * 100)

    dict_list1 = json.loads(json_data1)
    hpack_data = HPack.pack(dict_list1)
    print('经HPack算法压缩后的数据: ', json.dumps(hpack_data), '长度: ', len(json.dumps(hpack_data)))
    hpack_raw_data = HPack.unpack(hpack_data)
    print('解压后的数据: ', json.dumps(hpack_raw_data))

    print('-' * 100)

    jsonzip_hpack_data = JsonZip.Hpack_pack(dict_list1)
    print('HPack+gzip双重压缩后的数据: ', jsonzip_hpack_data, '长度: ', len(jsonzip_hpack_data))
    jsonzip_hpack_raw_data = JsonZip.Hpack_unpack(jsonzip_hpack_data)
    print('解压后的数据: ', json.dumps(jsonzip_hpack_raw_data))

    print('-' * 100)

    print('经HPack算法压缩后的数据压缩比: ', len(json.dumps(hpack_data))/len(json_data1))
    print('经HPack+gzip双重压缩后的数据压缩比: ', len(jsonzip_hpack_data)/len(json_data1))
    
    print('-' * 100)
    print('\n\n')

    print('测试样例2')
    print('-' * 100)

    json_data2 = '[{"country": "China", "province": "Anhui"}, {"country": "China", "province": "Beijing", "food": "douzhi"}, {"country": "China", "province": "Haerbin", "food": "hongchang"}]'
    print('原始数据: ', json_data2, '长度: ', len(json_data2))

    print('-' * 100)

    dict_list2 = json.loads(json_data2)
    cjson_data = CJson.pack(dict_list2)
    print('经CJson算法压缩后的数据: ', json.dumps(cjson_data), '长度: ', len(json.dumps(cjson_data)))
    cjson_raw_data = CJson.unpack(cjson_data)
    print('解压后的数据: ', json.dumps(cjson_raw_data))

    print('-' * 100)

    jsonzip_cjson_data = JsonZip.Cjson_pack(dict_list2)
    print('CJson+gzip双重压缩后的数据: ', jsonzip_cjson_data, '长度: ', len(jsonzip_cjson_data))
    jsonzip_cjson_raw_data = JsonZip.Cjson_unpack(jsonzip_cjson_data)
    print('解压后的数据: ', json.dumps(jsonzip_cjson_raw_data))

    print('-' * 100)

    print('经CJson算法压缩后的数据压缩比: ', len(json.dumps(cjson_data))/len(json_data2))
    print('经CJson+gzip双重压缩后的数据压缩比: ', len(jsonzip_cjson_data)/len(json_data2))

    print('-' * 100)