from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_iris
from ydata_profiling import ProfileReport

# 脚本所在目录，报告固定输出到此目录，避免受运行时工作目录影响
BASE_DIR: Path = Path(__file__).resolve().parent

# 设置中文显示（Windows）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------------- 1.读取数据 ----------------------
# 方式1：读取本地csv，改成你的文件路径
# df = pd.read_csv("your_data.csv")


def load_iris_dataframe() -> pd.DataFrame:
    """方式2：加载内置鸢尾花演示数据集，整理为带 target 列的 DataFrame。

    说明：sklearn 1.9 未为 load_iris 提供类型存根，类型检查器会将其返回值
    误判为元组类型，这里用 cast 显式声明为 Any 切断误报，其余逻辑保持类型安全。
    """
    iris_bunch: Any = cast(Any, load_iris())
    # 显式转为 ndarray，让 pandas 的构造重载能正确匹配
    data: np.ndarray = np.asarray(iris_bunch.data)
    target: np.ndarray = np.asarray(iris_bunch.target)
    feature_names: list[str] = [str(name) for name in iris_bunch.feature_names]
    frame: pd.DataFrame = pd.DataFrame(data=data, columns=pd.Index(feature_names))
    frame["target"] = target
    return frame


df: pd.DataFrame = load_iris_dataframe()

# ---------------------- 2.基础概览 ----------------------
print("===== 前5行数据 =====")
print(df.head())

print("\n===== 数据基本信息(类型、缺失) =====")
print(df.info())

print("\n===== 数值字段统计描述 =====")
print(df.describe())

print("\n===== 缺失值统计 =====")
print(df.isnull().sum())

print("\n===== 重复行数量 =====")
print("重复行数：", df.duplicated().sum())

# ---------------------- 3.单变量分析 ----------------------
# 直方图：数值分布
plt.figure(figsize=(12, 8))
for i, col in enumerate(df.columns[:-1]):
    plt.subplot(2, 2, i+1)
    sns.histplot(data=df, x=col, kde=True)
    plt.title(f"{col} 分布直方图")
plt.tight_layout()
plt.show()

# 箱线图：查看异常值
plt.figure(figsize=(12, 8))
for i, col in enumerate(df.columns[:-1]):
    plt.subplot(2, 2, i+1)
    sns.boxplot(data=df, y=col)
    plt.title(f"{col} 箱线图(异常值检测)")
plt.tight_layout()
plt.show()

# ---------------------- 4.双变量&相关性分析 ----------------------
corr: pd.DataFrame = df.corr()
print("\n===== 相关系数矩阵 =====")
print(corr)

# 相关性热力图
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("特征相关性热力图")
plt.show()

# 散点图矩阵（返回 PairGrid 对象，此处无需使用，显式赋值给 _ 避免未使用告警）
_ = sns.pairplot(df, hue="target")
plt.suptitle("特征配对散点图", y=1.02)
plt.show()

# ---------------------- 5.一键生成全自动EDA报告(可选) ----------------------
report_path: Path = BASE_DIR / "eda_report.html"
profile: ProfileReport = ProfileReport(df, title="EDA探索分析报告")
profile.to_file(report_path)
print(f"\nEDA报告已生成 {report_path}，浏览器打开即可查看")

