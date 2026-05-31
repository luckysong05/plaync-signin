"""Excel cross-tab lookup logic.

Tab 1 (身份信息): machine, name, phone, birthday, sex, carrier
Tab 2 (账号密码): phone, machine, account(email), password, comment

Flow: email → search Tab2.C → get password/phone → search Tab1.C → get identity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd


_cache: dict[tuple[str, float], tuple[pd.DataFrame, pd.DataFrame]] = {}


@dataclass
class LookupResult:
    email: str
    password: str = ""
    phone: str = ""
    machine: str = ""
    name: str = ""
    birthday: str = ""
    sex: int = 0
    carrier: str = ""
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error

    @property
    def birthday_label(self) -> str:
        if not self.birthday:
            return "—"
        b = self.birthday.replace(".0", "")
        if len(b) == 6:
            return f"{b[:2]}/{b[2:4]}/{b[4:6]}"
        return b


def load_excel(path: str | Path) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], str]:
    """Load both tabs from Excel. Cached on path + mtime."""
    path = Path(path)
    if not path.exists():
        return None, None, f"File not found: {path}"

    mtime = path.stat().st_mtime
    cache_key = (str(path.resolve()), mtime)
    if cache_key in _cache:
        return *_cache[cache_key], ""

    try:
        xls = pd.ExcelFile(path)
        sheet_names = [s.strip() for s in xls.sheet_names]
        if "身份信息" not in sheet_names or "账号密码" not in sheet_names:
            return None, None, f"Expected tabs '身份信息' and '账号密码', got {sheet_names}"

        df_id = pd.read_excel(path, sheet_name="身份信息", dtype=str)
        df_ac = pd.read_excel(path, sheet_name="账号密码", dtype=str)
        _cache[cache_key] = (df_id, df_ac)
        return df_id, df_ac, ""
    except Exception as e:
        return None, None, f"Failed to read Excel: {e}"


def search_accounts(df: pd.DataFrame, email: str) -> Optional[dict]:
    """Search 账号密码 tab by email (账号 column). Returns first match."""
    if df is None or df.empty or "账号" not in df.columns:
        return None

    col = "账号"
    mask = df[col].astype(str).str.strip().str.lower() == email.strip().lower()
    matches = df[mask]
    if matches.empty:
        return None

    row = matches.iloc[0]
    return {
        "phone": str(row.get("电话", "")).strip(),
        "machine": str(row.get("机器号", "")).strip(),
        "account": str(row.get("账号", "")).strip(),
        "password": str(row.get("密码", "")).strip(),
    }


def search_identity(df: pd.DataFrame, phone: str) -> Optional[dict]:
    """Search 身份信息 tab by phone (电话号 column). Returns first match."""
    if df is None or df.empty or "电话号" not in df.columns:
        return None

    mask = df["电话号"].astype(str).str.strip() == phone.strip()
    matches = df[mask]
    if matches.empty:
        return None

    row = matches.iloc[0]
    return {
        "machine": str(row.get("机器号", "")).strip(),
        "name": str(row.get("名字", "")).strip(),
        "phone": str(row.get("电话号", "")).strip(),
        "birthday": str(row.get("生日", "")).strip(),
        "sex": int(row.get("性别", 0) or 0),
        "carrier": str(row.get("通讯台", "")).strip(),
    }


def lookup(email: str, excel_path: str | Path) -> LookupResult:
    """Full cross-tab lookup: email → account → identity."""
    df_id, df_ac, err = load_excel(excel_path)
    if err:
        return LookupResult(email=email, error=err)

    acct = search_accounts(df_ac, email)
    if acct is None:
        return LookupResult(email=email, error=f"Email not found: {email}")

    phone = acct.get("phone", "")
    identity = search_identity(df_id, phone) if phone else None

    return LookupResult(
        email=email,
        password=acct.get("password", ""),
        phone=phone,
        machine=acct.get("machine", "") or (identity.get("machine", "") if identity else ""),
        name=identity.get("name", "") if identity else "",
        birthday=identity.get("birthday", "") if identity else "",
        sex=identity.get("sex", "") if identity else "",
        carrier=identity.get("carrier", "") if identity else "",
    )
