[Python API](https://googleapis.dev/python/protobuf/latest/), 
[Python Tutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial), 
[Python Pb Guide](https://www.datascienceblog.net/post/programming/essential-protobuf-guide-python/)



### python API

import pathlib
import os
from subprocess import check_call

def generate_proto_code():
    proto_interface_dir = "./src/interfaces"
    generated_src_dir = "./src/generated/"
    out_folder = "src"
    if not os.path.exists(generated_src_dir):
        os.mkdir(generated_src_dir)
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    proto_path = "generated=" + proto_interface_dir
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    check_call(["protoc"] + protos + ["--python_out", out_folder, "--proto_path", proto_path])
    
from setuptools.command.develop import develop
from setuptools import setup, find_packages

class CustomDevelopCommand(develop):
    """Wrapper for custom commands to run before package installation."""
    uninstall = False

    def run(self):
        develop.run(self)

    def install_for_development(self):
        develop.install_for_development(self)
        generate_proto_code()

setup(
    name='testpkg',
    version='1.0.0',
    package_dir={'': 'src'},
    cmdclass={
        'develop': CustomDevelopCommand, # used for pip install -e ./
    },
    packages=find_packages(where='src')
)

import addressbook_pb2
person = addressbook_pb2.Person()
person.id = 1234
person.name = "John Doe"
person.email = "jdoe@example.com"
phone = person.phones.add()
phone.number = "555-4321"
phone.type = addressbook_pb2.Person.HOME


# python动态解析oneof字段

data = getattr(config, config.WhichOneof('config')).value

# Note:
*	SetInParent()
* Wrapping protocol buffers is also a good idea if you don't have control over the design of the `.proto` file'
* You should never add behaviour to the generated classes by inheriting from them


# serialize proto object
import os
out_dir = "proto_dump"
with open(os.path.join(out_dir, "person.pb"), "wb") as f:
    # binary output
    f.write(person.SerializeToString())
with open(os.path.join(out_dir, "person.protobuf"), "w") as f:
    # human-readable output for debugging
    # by default, entries with a value of 0 are never printed
    f.write(str(person))
