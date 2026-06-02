"""
修正长顺县实体坐标

敦操乡民族学校和打召村的坐标原先落在惠水县GeoJSON多边形内，
修正为长顺县多边形区域内的正确坐标。
"""
import sqlite3
import os
import glob

# 坐标修正映射：(old_lat, old_lng) -> (new_lat, new_lng)
FIXES = [
    # 敦操乡民族学校 (schools.id=20, district=长顺县)
    # 原坐标 (25.8392, 106.5043) 落在惠水县 -> 修正到长顺县南部
    {
        "table": "schools",
        "id": 20,
        "name": "敦操乡民族学校",
        "old_lat": 25.8392,
        "old_lng": 106.5043,
        "new_lat": 25.9300,
        "new_lng": 106.3000,
    },
    # 打召村 (supported_villages.id=18, county=长顺县)
    # 原坐标 (25.8224, 106.5183) 落在惠水县 -> 修正到长顺县南部
    {
        "table": "supported_villages",
        "id": 18,
        "name": "打召村",
        "old_lat": 25.8224,
        "old_lng": 106.5183,
        "new_lat": 25.8800,
        "new_lng": 106.3500,
    },
]


def fix_coords(db_path: str) -> int:
    """修正指定数据库中的坐标，返回更新行数"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    total = 0

    for fix in FIXES:
        table = fix["table"]

        # 检查表是否存在
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        if not cur.fetchone():
            continue

        # 检查记录是否存在且坐标匹配旧值
        cur.execute(
            f"SELECT id, latitude, longitude FROM {table} WHERE id=?",
            (fix["id"],),
        )
        row = cur.fetchone()
        if not row:
            continue

        cur_lat, cur_lng = row[1], row[2]
        # 仅在坐标是旧值时更新（避免重复执行覆盖用户手动修正）
        if (
            cur_lat is not None
            and cur_lng is not None
            and abs(cur_lat - fix["old_lat"]) < 0.001
            and abs(cur_lng - fix["old_lng"]) < 0.001
        ):
            cur.execute(
                f"UPDATE {table} SET latitude=?, longitude=? WHERE id=?",
                (fix["new_lat"], fix["new_lng"], fix["id"]),
            )
            total += cur.rowcount
            print(
                f"  [{table}] {fix['name']} (id={fix['id']}): "
                f"({cur_lat}, {cur_lng}) -> ({fix['new_lat']}, {fix['new_lng']})"
            )
        else:
            print(
                f"  [{table}] {fix['name']} (id={fix['id']}): "
                f"skipped (current coords: {cur_lat}, {cur_lng})"
            )

    conn.commit()
    conn.close()
    return total


def main():
    # 查找所有包含相关表的数据库
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_paths = [
        os.path.join(base, "data", "rural_revitalization.db"),
        os.path.join(base, "backend", "data", "rural_revitalization.db"),
    ]

    for db_path in db_paths:
        if os.path.isfile(db_path):
            print(f"\nProcessing: {db_path}")
            updated = fix_coords(db_path)
            print(f"  Updated {updated} rows")
        else:
            print(f"\nSkipped (not found): {db_path}")


if __name__ == "__main__":
    main()
