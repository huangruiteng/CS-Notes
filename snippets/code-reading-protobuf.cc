* C++程序路径是 src/google/protobuf

总图参考【code-reading.md】- protobuf
* 箭头描述了根据 type name 反射创建具体 Message 对象的过程
  * 【设计模式】中的prototype pattern
  * 获取instance：MessageFactory::GetPrototype (const Descriptor*)
  * 拿到Descriptor*: DescriptorPool 中根据 type name 查到 Descriptor
  * 相关不变式：chenshuo/recipes/protobuf/descriptor_test.cc



* message.*
  * MessageLite
    * ByteSizeLong()
    * SerializeWithCachedSizesToArray() 内部使用上次调用的 ByteSizeLong 结果
  * Message
    * prototype->New()
  * MessageFactory
    * GetPrototype: 线程安全性依赖于实现
    * 但是 MessageFactory::generated_factory() 获取的 factroy 是 100% 线程安全的
* Descriptor：主要是对 Message 进行描述，包括 message 的名字、所有字段的描述、原始 proto 文件内容等
  * `FieldDescriptor* field(int index)`和`FieldDescriptor* FindFieldByNumber(int number)`这个函数中`index`和`number`的含义是不一样的
    * 某个例子：index为2、number为5是tag number

  * `Descriptor::DebugString()`

* FieldDescriptor：要是对 Message 中单个字段进行描述，包括字段名、字段属性、原始的 field 字段等

```c++
OneofDescriptor* type = descriptor->FindOneofByName("type");
FieldDescriptor* type_field = reflection->GetOneofFieldDescriptor(*conf, type);

FindFieldByName
```

```c++
const std::string & name() const; // Name of this field within the message.
const std::string & lowercase_name() const; // Same as name() except converted to lower-case.
const std::string & camelcase_name() const; // Same as name() except converted to camel-case.
CppType cpp_type() const; //C++ type of this field.

enum FieldDescriptor::Type;
  
bool is_required() const; // 判断字段是否是必填
bool is_optional() const; // 判断字段是否是选填
bool is_repeated() const; // 判断字段是否是重复值

const FieldOptions & FieldDescriptor::options() const
```



* dynamic_message.*
  * use Reflection to implement our reflection interface
  * Any Descriptors used with a particular factory must outlive the factory.
  * DynamicMessage
    * 构造时 type_info->prototype = this;，处理cyclic dependency
    * CrossLinkPrototypes: allows for fast reflection access of unset message fields. Without it we would have to go to the MessageFactory to get the prototype, which is a much more expensive operation.
    * Line427: 似乎认为map的label是repeated

  * DynamicMessageFactory
    * GetPrototypeNoLock
      * 调用 DynamicMessage(DynamicMessageFactory::TypeInfo* type_info, bool lock_factory);
      * !type->oneof_decl(i)->is_synthetic() --> real_oneof
      * 建立reflection

  * Note:
    * This module often calls "operator new()" to allocate untyped memory, rather than calling something like "new uint8_t[]". 主要考虑是aligned问题，参考【C++笔记】《More Effective C++》 item 8


```c++
// 内存对齐
inline int DivideRoundingUp(int i, int j) { return (i + (j - 1)) / j; }

static const int kSafeAlignment = sizeof(uint64_t);

inline int AlignTo(int offset, int alignment) {
  return DivideRoundingUp(offset, alignment) * alignment;
}

// Rounds the given byte offset up to the next offset aligned such that any
// type may be stored at it.
inline int AlignOffset(int offset) { return AlignTo(offset, kSafeAlignment); }
```

* CodedStream
  * CodedInputStream::ReadString，优化 string 的 initialize
    * [相关 C++ proposal](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1072r1.html)
    * `absl::strings_internal::STLStringResizeUninitialized(buffer, size);`
    * __resize_default_init is provided by libc++ >= 8.0
  * [ZeroCopyInputStream](https://groups.google.com/g/protobuf/c/IzGj73Jk14I)
    * All of the SerializeTo*() methods simply construct a ZeroCopyOutputStream of the desired type and then call SerializeToZeroCopyStream(). 
    * 核心是避免在parse之前stream copy的开销
  * SIMD优化protobuf::CodedInputStream::ReadVarint64Fallback
    * https://tech.meituan.com/2022/03/24/tensorflow-gpu-training-optimization-practice-in-meituan-waimai-recommendation-scenarios.html

* repeated_field.h

```c++
AddAllocatedInternal()
// arena 一样则 zero copy
// if current_size < allocated_size，Make space at [current] by moving first allocated element to end of allocated list.
    
// DeleteSubgrange，注意性能
template <typename Element>
inline void RepeatedPtrField<Element>::DeleteSubrange(int start, int num) {
  GOOGLE_DCHECK_GE(start, 0);
  GOOGLE_DCHECK_GE(num, 0);
  GOOGLE_DCHECK_LE(start + num, size());
  for (int i = 0; i < num; ++i) {
    RepeatedPtrFieldBase::Delete<TypeHandler>(start + i);
  }
  ExtractSubrange(start, num, NULL);
}

mutable_obj()->Add()->CopyFrom(*old_objptr);
mutable_obj()->AddAllocated(old_objptr);
```

* Reflection：message.h + generated_message_reflection.cc
  * [讲解pb的反射](https://zhuanlan.zhihu.com/p/302771012)，提供了动态读、写 message 中单个字段能力
  * modify the fields of the Message dynamically, in other words, without knowing the message type at compile time
  * 使用时要求API的精准使用，并没有一个general的Field抽象，主要是考虑性能问题
    * Set/Get Int32/String/Message/Repeated...
    * AddInt32/String/... for repeated field
    * `void Reflection::ListFields(const Message & message, std::vector< const FieldDescriptor * > * output) const`

  * 场景：
    * 获取pb中所有非空字段
    * 将字段校验规则放在proto中
    * 基于 PB 反射的前端页面自动生成方案
    * 通用存储系统：快速加字段。。pb存到非关系型数据库


```protobuf
import "google/protobuf/descriptor.proto";

extend google.protobuf.FieldOptions {
  optional uint32 attr_id              = 50000; //字段id
  optional bool is_need_encrypt        = 50001 [default = false]; // 字段是否加密,0代表不加密，1代表加密
  optional string naming_conventions1  = 50002; // 商户组命名规范
  optional uint32 length_min           = 50003  [default = 0]; // 字段最小长度
  optional uint32 length_max           = 50004  [default = 1024]; // 字段最大长度
  optional string regex                = 50005; // 该字段的正则表达式
}

message SubMerchantInfo {
  // 商户名称
  optional string merchant_name = 1 [
    (attr_id) = 1,
    (is_encrypt) = 0,
    (naming_conventions1) = "company_name",
    (length_min) = 1,
    (length_max) = 80,
    (regex.field_rules) = "[a-zA-Z0-9]"
  ];
}

#include <google/protobuf/descriptor.h>
#include <google/protobuf/message.h>

std::string strRegex = FieldDescriptor->options().GetExtension(regex);
uint32 dwLengthMinp = FieldDescriptor->options().GetExtension(length_min);
bool bIsNeedEncrypt = FieldDescriptor->options().GetExtension(is_need_encrypt);
```

```c++
#include "pb_util.h"

#include <sstream>

namespace comm_tools {
int PbToMap(const google::protobuf::Message &message,
            std::map<std::string, std::string> &out) {
#define CASE_FIELD_TYPE(cpptype, method, valuetype)                            \
  case google::protobuf::FieldDescriptor::CPPTYPE_##cpptype: {                 \
    valuetype value = reflection->Get##method(message, field);                 \
    std::ostringstream oss;                                                    \
    oss << value;                                                              \
    out[field->name()] = oss.str();                                            \
    break;                                                                     \
  }

#define CASE_FIELD_TYPE_ENUM()                                                 \
  case google::protobuf::FieldDescriptor::CPPTYPE_ENUM: {                      \
    int value = reflection->GetEnum(message, field)->number();                 \
    std::ostringstream oss;                                                    \
    oss << value;                                                              \
    out[field->name()] = oss.str();                                            \
    break;                                                                     \
  }

#define CASE_FIELD_TYPE_STRING()                                               \
  case google::protobuf::FieldDescriptor::CPPTYPE_STRING: {                    \
    std::string value = reflection->GetString(message, field);                 \
    out[field->name()] = value;                                                \
    break;                                                                     \
  }

  const google::protobuf::Descriptor *descriptor = message.GetDescriptor();
  const google::protobuf::Reflection *reflection = message.GetReflection();
  for (int i = 0; i < descriptor->field_count(); i++) {
    const google::protobuf::FieldDescriptor *field = descriptor->field(i);
    bool has_field = reflection->HasField(message, field);

    if (has_field) {
      if (field->is_repeated()) {
        return -1; // 不支持转换repeated字段
      }

      const std::string &field_name = field->name();
      switch (field->cpp_type()) {
        CASE_FIELD_TYPE(INT32, Int32, int);
        CASE_FIELD_TYPE(UINT32, UInt32, uint32_t);
        CASE_FIELD_TYPE(FLOAT, Float, float);
        CASE_FIELD_TYPE(DOUBLE, Double, double);
        CASE_FIELD_TYPE(BOOL, Bool, bool);
        CASE_FIELD_TYPE(INT64, Int64, int64_t);
        CASE_FIELD_TYPE(UINT64, UInt64, uint64_t);
        CASE_FIELD_TYPE_ENUM();
        CASE_FIELD_TYPE_STRING();
      default:
        return -1; // 其他异常类型
      }
    }
  }

  return 0;
}
} // namespace comm_tools
```

```protobuf
syntax = "proto2";

package student;

import "google/protobuf/descriptor.proto";

message FieldRule{
    optional uint32 length_min = 1; // 字段最小长度
    optional uint32 id         = 2; // 字段映射id
}

extend google.protobuf.FieldOptions{
    optional FieldRule field_rule = 50000;
}

message Student{
    optional string name   =1 [(field_rule).length_min = 5, (field_rule).id = 1];
    optional string email = 2 [(field_rule).length_min = 10, (field_rule).id = 2];
}
```

```c++
Message* msg = reflection->MutableMessage(original_msg, my_field);
FieldDescriptor* target_field = XXX;
msg->GetReflection()->SetInt32(msg, target_field, value)
```



#### encode/decode

* varint
  * int32的变长编码算法如下，负数编码位数高，建议用sint32
  * sint32的变长编码，通过Zigzag编码将有符号整型映射到无符号整型

```java
const maxVarintBytes = 10 // maximum length of a varint

func EncodeVarint(x uint64) []byte {
        var buf [maxVarintBytes]byte
        var n int
        for n = 0; x > 127; n++ {
                // 首位记 1, 写入原始数字从低位始的 7 个 bit
                buf[n] = 0x80 | uint8(x&0x7F)
                // 移走记录过的 7 位
                x >>= 7
        }
        // 剩余不足 7 位的部分直接以 8 位形式存下来，故首位为 0
        buf[n] = uint8(x)
        n++
        return buf[0:n]
}

func Zigzag64(x uint64) uint64 {
        // 左移一位 XOR (-1 / 0 的 64 位补码)，正负数映射到无符号的奇偶数
        // 若 x 为负数，XOR 左边为 -x 的补码左移一位
        return (x << 1) ^ uint64(int64(x) >> 63)
}
```

* float 5 byte，double 9 byte
* fixed64: 大于 2^56 的数，用 fixed64，因为varint有浪费
* map/list v.s. embedded message
  * embedded message: 显式在字段内将key穷举，用optional
  * map/list：自己
* 字段号对存储的影响
  * message 的二进制流中使用字段号（field's number 和 wire_type -- 3bit）作为 key。同时key采用varint编码方式'
  * Tag: (field_num << 3) | wire_type
* 对标准整数repeated类型开packed=true（proto3默认开）
  *  tag + length + content + content + content，tag只出现一次
  *  python/google/protobuf/internal/wire_type.py
  *  WIRETYPE_LENGTH_DELIMITED: key + length + context
     * string,byted,embedded messages, packed repeated fields




WIRETYPE_VARINT = 0
WIRETYPE_FIXED64 = 1
WIRETYPE_LENGTH_DELIMITED = 2
WIRETYPE_START_GROUP = 3
WIRETYPE_END_GROUP = 4
WIRETYPE_FIXED32 = 5
_WIRETYPE_MAX = 5

# Maps from field type to expected wiretype.
FIELD_TYPE_TO_WIRE_TYPE = {
    _FieldDescriptor.TYPE_DOUBLE: wire_format.WIRETYPE_FIXED64,
    _FieldDescriptor.TYPE_FLOAT: wire_format.WIRETYPE_FIXED32,
    _FieldDescriptor.TYPE_INT64: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_UINT64: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_INT32: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_FIXED64: wire_format.WIRETYPE_FIXED64,
    _FieldDescriptor.TYPE_FIXED32: wire_format.WIRETYPE_FIXED32,
    _FieldDescriptor.TYPE_BOOL: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_STRING:
      wire_format.WIRETYPE_LENGTH_DELIMITED,
    _FieldDescriptor.TYPE_GROUP: wire_format.WIRETYPE_START_GROUP,
    _FieldDescriptor.TYPE_MESSAGE:
      wire_format.WIRETYPE_LENGTH_DELIMITED,
    _FieldDescriptor.TYPE_BYTES:
      wire_format.WIRETYPE_LENGTH_DELIMITED,
    _FieldDescriptor.TYPE_UINT32: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_ENUM: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_SFIXED32: wire_format.WIRETYPE_FIXED32,
    _FieldDescriptor.TYPE_SFIXED64: wire_format.WIRETYPE_FIXED64,
    _FieldDescriptor.TYPE_SINT32: wire_format.WIRETYPE_VARINT,
    _FieldDescriptor.TYPE_SINT64: wire_format.WIRETYPE_VARINT,
    }



