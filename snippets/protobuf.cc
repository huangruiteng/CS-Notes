
//// usage

[Language Guide](https://developers.google.com/protocol-buffers/docs/proto3)

[API Reference](https://developers.google.com/protocol-buffers/docs/reference/overview)


protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto

* 一种常见使用方式：protoc提前编译好.proto文件

* 不常见的方式：codex读取.proto文件在线解析message

  * https://cxwangyi.blogspot.com/2010/06/google-protocol-buffers-proto.html

  * 自己实现 GetMessageTypeFromProtoFile，由 .proto 获取 FileDescriptorProto

* 限制：序列化大小不超过2GB

const int kMaxRecieveBufferSize = 32 * 1024 * 1024;  // 32MB
static char buffer[kMaxRecieveBufferSize];
...
google::protobuf::DescriptorPool pool;
const google::protobuf::FileDescriptor* file_desc = pool.BuildFile(file_desc_proto);
const google::protobuf::Descriptor* message_desc = file_desc->FindMessageTypeByName(message_name);

google::protobuf::DynamicMessageFactory factory;
const google::protobuf::Message* prototype_msg = factory.GetPrototype(message_desc);
mutable_message = prototype->New();
...
input_stream.read(buffer, proto_msg_size);
mutable_msg->ParseFromArray(buffer, proto_msg_size)


// CreateMessage

::google::protobuf::ArenaOptions arena_opt;
arena_opt.start_block_size = 8192;
arena_opt.max_block_size = 8192;
google::protobuf::Arena local_arena(arena_opt);
auto* mini_batch_proto = google::protobuf::Arena::CreateMessage<myProto>(&local_arena);


* Note:
	* scalar type有默认值
	* 对于新增的optional type，需要注意加`[default = value]`或者用has方法判断是否存在
	* allow_alias: 允许alias，属性的数字相同
	* reserved values

* Importing Definitions

  * 允许import proto2，但不能直接在proto3用proto2 syntax

  * import public允许pb的替换


```protobuf
// old.proto
// This is the proto that all clients are importing.
import public "new.proto";
import "other.proto";
```

* Nested Types

```protobuf
message SearchResponse {
  message Result {
    string url = 1;
    string title = 2;
    repeated string snippets = 3;
  }
  repeated Result results = 1;
}

message SomeOtherMessage {
  SearchResponse.Result result = 1;
}
```

* Any Type

```c++
import "google/protobuf/any.proto";

message ErrorStatus {
  string message = 1;
  repeated google.protobuf.Any details = 2;
}

// Storing an arbitrary message type in Any.
NetworkErrorDetails details = ...;
ErrorStatus status;
status.add_details()->PackFrom(details);
// Reading an arbitrary message from Any.
ErrorStatus status = ...;
for (const Any& detail : status.details()) {
  if (detail.Is<NetworkErrorDetails>()) {
    NetworkErrorDetails network_error;
    detail.UnpackTo(&network_error);
    ... processing network_error ...
  }
}
```

* Oneof Type

  * Changing a single value into a member of a new oneof is safe and binary compatible. Moving multiple fields into a new oneof may be safe if you are sure that no code sets more than one at a time. Moving any fields into an existing oneof is not safe.

  * 用 TypeCase来判断OneOf类型

  * 小心oneof出core，设了另一个field会把原先的删掉，不能再设原先的内部field

  * [Backwards-compatibility issues](https://developers.google.com/protocol-buffers/docs/proto3#backwards-compatibility_issues)


* Map Type

  * When parsing from the wire or when merging, if there are duplicate map keys the last key seen is used. When parsing a map from text format, parsing may fail if there are duplicate keys.

  * Backwards compatibility

```protobuf
message MapFieldEntry {
  key_type key = 1;
  value_type value = 2;
}

repeated MapFieldEntry map_field = N;
```

* Packages

  * 相当于C++的namespace

  * `foo.bar.Open`，从后往前搜索，先搜索bar再搜索foo，如果是`.foo.bar.Open`，则从前往后搜索

```protobuf
package foo.bar;
message Open { ... }

message Foo {
  ...
  foo.bar.Open open = 1;
  ...
}
```


* options
	- google/protobuf/descriptor.proto

option optimize_for = CODE_SIZE; //SPEED(DEFAULT), LITE_RUNTIME
option cc_enable_arenas = true;
int32 old_field = 6 [deprecated = true];

//// debug

ShortDebugString()


//// example

syntax = "proto3";

message SearchRequest {
  string query = 1;
  int32 page_number = 2;
  int32 result_per_page = 3;
  enum Corpus {
    UNIVERSAL = 0;
    WEB = 1;
    IMAGES = 2;
    LOCAL = 3;
    NEWS = 4;
    PRODUCTS = 5;
    VIDEO = 6;
  }
  Corpus corpus = 4;
}

message MyMessage1 {
  enum EnumAllowingAlias {
    option allow_alias = true;
    UNKNOWN = 0;
    STARTED = 1;
    RUNNING = 1;
  }
}

enum Foo {
  reserved 2, 15, 9 to 11, 40 to max;
  reserved "FOO", "BAR";
}


//// rpc service

service SearchService {
  rpc Search(SearchRequest) returns (SearchResponse);
}

// client code
using google::protobuf;

protobuf::RpcChannel* channel;
protobuf::RpcController* controller;
SearchService* service;
SearchRequest request;
SearchResponse response;

void DoSearch() {
  // You provide classes MyRpcChannel and MyRpcController, which implement
  // the abstract interfaces protobuf::RpcChannel and protobuf::RpcController.
  channel = new MyRpcChannel("somehost.example.com:1234");
  controller = new MyRpcController;

  // The protocol compiler generates the SearchService class based on the
  // definition given above.
  service = new SearchService::Stub(channel);

  // Set up the request.
  request.set_query("protocol buffers");

  // Execute the RPC.
  service->Search(controller, request, response, protobuf::NewCallback(&Done));
}

void Done() {
  delete service;
  delete channel;
  delete controller;
}

// service code
using google::protobuf;

class ExampleSearchService : public SearchService {
 public:
  void Search(protobuf::RpcController* controller,
              const SearchRequest* request,
              SearchResponse* response,
              protobuf::Closure* done) {
    if (request->query() == "google") {
      response->add_result()->set_url("http://www.google.com");
    } else if (request->query() == "protocol buffers") {
      response->add_result()->set_url("http://protobuf.googlecode.com");
    }
    done->Run();
  }
};

int main() {
  // You provide class MyRpcServer.  It does not have to implement any
  // particular interface; this is just an example.
  MyRpcServer server;

  protobuf::Service* service = new ExampleSearchService;
  server.ExportOnPort(1234, service);
  server.Run();

  delete service;
  return 0;
}



//// 内存泄漏调研

- 对一个长期存在的proto message对象进行多次repeated field相关操作，内存会持续增长
  - https://github.com/protocolbuffers/protobuf/issues/10294
  - https://brunocalza.me/what-zero-copy-serialization-means/
- 使用arena create的protobuf对象，如果swap了一个非arena create的对象也会产生僵尸内存，导致内存增长
  - https://linux.do/t/topic/25107/2 (只言片语，缺失代码分析)
- `set_allocated_XXX/release_XXX` 可能导致内存泄漏
  - https://cloud.tencent.com/developer/article/1747458


