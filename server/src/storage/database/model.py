"""
数据库模型定义
"""
from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from coze_coding_dev_sdk.database import Base


class HealthCheck(Base):
    """系统健康检查表（Supabase系统表，禁止删除）"""
    __tablename__ = "health_check"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class IndustrySector(Base):
    """行业板块表"""
    __tablename__ = "industry_sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="行业名称")
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, comment="行业代码")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index("ix_industry_sectors_name", "name"),
        Index("ix_industry_sectors_code", "code"),
    )


class IndustryDailyData(Base):
    """行业每日数据表"""
    __tablename__ = "industry_daily_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sector_code: Mapped[str] = mapped_column(String(20), nullable=False, comment="行业代码")
    trade_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="交易日期(YYYY-MM-DD)")
    open_price: Mapped[float] = mapped_column(Float, nullable=False, comment="开盘价")
    high_price: Mapped[float] = mapped_column(Float, nullable=False, comment="最高价")
    low_price: Mapped[float] = mapped_column(Float, nullable=False, comment="最低价")
    close_price: Mapped[float] = mapped_column(Float, nullable=False, comment="收盘价")
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="成交量")
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment="成交额")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index("ix_industry_daily_data_sector_code", "sector_code"),
        Index("ix_industry_daily_data_trade_date", "trade_date"),
        Index("ix_industry_daily_data_sector_date", "sector_code", "trade_date", unique=True),
    )
