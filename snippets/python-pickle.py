
# pickle attribute error

https://stackoverflow.com/questions/27732354/unable-to-load-files-using-pickle-and-multiple-modules/51397373#51397373

import pickle

class CustomUnpickler(pickle.Unpickler):

    def find_class(self, module, name):
        if name == 'Manager':
            from settings import Manager
            return Manager
        return super().find_class(module, name)

pickle_data = CustomUnpickler(open('file_path.pkl', 'rb')).load()