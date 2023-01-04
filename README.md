# JsonTools
Json数据压缩工具

## 简介
- 本工具实现了使用HPack算法和CJson算法对json数据的压缩与解压，并在上述两种压缩算法的基础上进行了gzip压缩，从而实现更小压缩率的json数据压缩。

## 算法简介
- CJson算法是将json数据的key和value抽离成Template与Value，并将重复的key去掉，从而实现json数据压缩。
- - 例子：[{"x": 100, "y": 100}, {"x": 200, "y": 200, "height": 3, "width": 4}] 经CJson算法压缩为 {"t": [[0, "x", "y"], [1, "height", "width"]], "v": [[1, 100, 100], [2, 200, 200, 3, 4]]}
- HPack算法适用于泛型同构集合，它也是将json数据的key和value抽离成Template与Value，不过由于集合是泛型同构的，所以所有集合的keys都是一样的，因此只需要记录一组keys和所有的values。
- - 例子：[{"a": "A", "b": "B"}, {"a": "C", "b": "D"}, {"a": "E", "b": "F"}] 经HPack算法压缩为 [2, "a", "b", "A", "B", "C", "D", "E", "F"]

## 使用说明
- 使用HPack算法对json数据进行压缩和解压：HPack.pack() HPack.unpack()
- 使用CJson算法对json数据进行压缩和解压：CJson.pack() CJson.unpack()
- 使用HPack+gzip对json数据进行压缩和解压：JsonZip.Hpack_pack() JsonZip.Hpack_unpack()
- 使用CJson+gzip对json数据进行压缩和解压：JsonZip.Cjson_pack() JsonZip.Cjson_unpack()  
ps: 统一json数据格式为存储dict的list