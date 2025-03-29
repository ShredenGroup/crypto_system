import os
import importlib
import sys
def get_strategy(name,**kwarg):
    if not name:
        print("策略名称为空")
        return None
        
    print(f"正在查找策略: {name}")
    for dirpath,_,filenames in os.walk(os.path.dirname(__file__)):
        print(f"当前目录下的文件: {filenames}")
        for filename in filenames:
            if filename.endswith("_strategy.py"):
                if filename.replace("_strategy.py","")==name:
                    print(f"找到匹配的策略文件: {filename}")
                    spec=importlib.util.spec_from_file_location(name,os.path.join(dirpath,filename))
                    module=importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    if not hasattr(module, 'Strategy'):
                        print(f"警告：{filename} 中没有找到 Strategy 类")
                        return None
                    return module.Strategy
    print(f"未找到策略: {name}")
    return None
