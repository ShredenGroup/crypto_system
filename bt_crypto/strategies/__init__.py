import os
import importlib
import sys
def get_strategy(name,**kwarg):
    for dirpath,_,filenames in os.walk(os.path.dirname(__file__)):
        for filename in filenames:
            if filename.endswith("_strategy.py"):
                if filename.replace("_strategy.py","")==name:
                    spec=importlib.util.spec_from_file_location(name,os.path.join(dirpath,filename))
                    module=importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    if module.Strategy is None:
                        print("it's None")
                    return module.Strategy
    return None
