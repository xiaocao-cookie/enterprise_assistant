from sqlalchemy.orm import DeclarativeBase

# DeclarativeBase 是 SQLAlchemy 2.X 的基础类，用于定义 ORM 模型的基类
# 所有的数据库表对应的模型类都应该继承它！！！
# 它提供了： 1

class Base(DeclarativeBase):
    """
    这是 SQLAlchemy 模型的基类，所有的数据库表对应的模型类都应该继承它！！！

    说明：
        DeclarativeBase 是 SQLAlchemy 2.X 的基础类，用于定义 ORM 模型的基类
        它提供了：
            1. 元数据的管理
            2. 表与模型类的映射
            3. ORM 所需的其他功能
    """
    pass