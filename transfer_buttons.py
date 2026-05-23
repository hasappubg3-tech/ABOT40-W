"""
سكريبت نقل الأزرار الداخلية من زر مدمج (مصدر) إلى زر مدمج آخر (وجهة)
- يُضيف الأزرار الداخلية من المصدر بعد الموجودة في الوجهة
- لا يحذف المحتوى الموجود في الوجهة
- لا يحذف المصدر
"""
import os
import sys
from pymongo import MongoClient, ASCENDING

MONGODB_URI = os.environ.get("MONGODB_URI", "")

client = MongoClient(MONGODB_URI)
db = client.get_default_database() if (
    "/" in MONGODB_URI.rsplit("@", 1)[-1] and
    MONGODB_URI.rsplit("/", 1)[-1].split("?")[0]
) else client["botdb"]

buttons = db["buttons"]

# قائمة الأزوج: (مصدر, وجهة)
PAIRS = [
    (2135, 1783),
    (2137, 1790),
    (2139, 1793),
    (2141, 1787),
    (2143, 1778),
    (2150, 1825),
    (2148, 1856),
    (2154, 1835),
    (2157, 1861),
    (2159, 1868),
    (2161, 1870),
    (2164, 1891),
    (2166, 1889),
    (2168, 1905),
    (2170, 1895),
    (2173, 1934),
    (2175, 1924),
    (2177, 1946),
    (2179, 1931),
    (2182, 1967),
    (2184, 1971),
    (2186, 1974),
    (2191, 2021),
]

def get_btn(bid):
    doc = buttons.find_one({"id": bid})
    return doc

def get_children(parent_id):
    """جلب الأزرار الداخلية مرتبة حسب ord"""
    return list(buttons.find({"parent_id": parent_id, "deleted": {"$ne": 1}}).sort([("ord", 1), ("id", 1)]))

def get_max_ord(parent_id):
    """جلب أعلى قيمة ord في الوجهة"""
    children = get_children(parent_id)
    if not children:
        return 0
    return max(c.get("ord", 0) for c in children)


errors = []
transferred_total = 0

for src_id, dst_id in PAIRS:
    src = get_btn(src_id)
    dst = get_btn(dst_id)

    # التحقق من وجود الزرين
    if not src:
        msg = f"  ❌ زر المصدر {src_id} غير موجود!"
        print(msg); errors.append(msg)
        continue
    if not dst:
        msg = f"  ❌ زر الوجهة {dst_id} غير موجود!"
        print(msg); errors.append(msg)
        continue

    src_label = src.get("label", "")
    dst_label = dst.get("label", "")
    src_type  = src.get("type", "")
    dst_type  = dst.get("type", "")

    print(f"\n{'='*60}")
    print(f"نقل من [{src_id}] «{src_label}» ({src_type})")
    print(f"     إلى [{dst_id}] «{dst_label}» ({dst_type})")

    # جلب الأزرار الداخلية للمصدر
    src_children = get_children(src_id)

    if not src_children:
        print(f"  ⚠️  المصدر {src_id} لا يحتوي على أزرار داخلية، تخطي.")
        continue

    # حساب أعلى ord موجود في الوجهة
    base_ord = get_max_ord(dst_id)
    print(f"  عدد أزرار المصدر: {len(src_children)}")
    print(f"  عدد أزرار الوجهة الحالية: {base_ord}")

    # نقل كل زر داخلي: تغيير parent_id وتحديث ord
    for i, child in enumerate(src_children, start=1):
        new_ord = base_ord + i
        child_id = child["id"]
        child_label = child.get("label", "")
        buttons.update_one(
            {"id": child_id},
            {"$set": {"parent_id": dst_id, "ord": new_ord}}
        )
        print(f"    ✅ نُقل [{child_id}] «{child_label}» → ord={new_ord}")
        transferred_total += 1

print(f"\n{'='*60}")
print(f"✅ اكتمل النقل: {transferred_total} زر داخلي منقول بنجاح")
if errors:
    print(f"\n⚠️  أخطاء ({len(errors)}):")
    for e in errors:
        print(e)

client.close()
