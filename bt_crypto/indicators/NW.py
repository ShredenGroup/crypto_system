import backtrader as bt
import numpy as np

class NW(bt.Indicator):
    """
    Nadaraya-Watson核回归指标（带上下界）
    """
    lines = ('nw', 'upper', 'lower')  # 添加上下界线
    params = (
        ('h', 6.0),     # 带宽参数
        ('mult', 3.0),  # 边界乘数
        ('period', 20), # 固定使用499个周期，与TV保持一致
    )
    
    # 添加绘图信息
    plotinfo = dict(
        subplot=False,  # 是否在主图上绘制
        plotname='NW Kernel',  # 指标名称
        plotabove=False,  # 是否在价格线上方绘制
    )
    
    # 设置线条样式
    plotlines = dict(
        nw=dict(
            _name='NW',  # 主线名称
            color='blue',  # 主线颜色
            linewidth=1.0,  # 线宽
        ),
        upper=dict(
            _name='Upper',  # 上界线名称
            color='gray',  # 上界线颜色
            linewidth=1.0,
            alpha=0.5,  # 透明度
            linestyle='--',  # 虚线样式
        ),
        lower=dict(
            _name='Lower',  # 下界线名称
            color='gray',  # 下界线颜色
            linewidth=1.0,
            alpha=0.5,
            linestyle='--',
        ),
    )
    
    def __init__(self):
        super().__init__()
        self.addminperiod(self.p.period)
    
    def gaussian_kernel(self, x):
        """
        高斯核函数
        K(u) = exp(-u^2 / (2h^2))
        """
        return np.exp(-x**2 / (2 * self.p.h**2))
    
    def next(self):
        """
        计算当前时刻的NW估计值及其上下界
        """
        # 获取最近period个时间点
        x = np.array(range(len(self)))[-self.p.period:]
        # 获取对应的价格数据
        y = np.array(self.data.get(size=self.p.period))
        
        target = x[-1]
        
        # 计算主线
        weights = self.gaussian_kernel(x - target)
        numerator = np.sum(weights * y)
        denominator = np.sum(weights)
        nw_value = numerator / denominator
        
        # 计算移动平均绝对误差
        errors = np.abs(y - nw_value)
        mae = np.mean(errors) * self.p.mult
        
        # 设置指标值
        self.lines.nw[0] = nw_value
        self.lines.upper[0] = nw_value + mae
        self.lines.lower[0] = nw_value - mae