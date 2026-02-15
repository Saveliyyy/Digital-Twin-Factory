import pkg_resources
import sys

print("=" * 60)
print("ПРОВЕРКА ВЕРСИЙ ПАКЕТОВ")
print("=" * 60)

installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

with open('requirements.txt', 'r') as f:
    required = {}
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if '==' in line:
                name, version = line.split('==')
                name = name.strip().lower()
                required[name] = version
            elif '>=' in line or '<=' in line:
                name = line.split('[')[0].split('<')[0].split('>')[0].strip().lower()
                required[name] = 'specified with range'

print("\n📦 СРАВНЕНИЕ ВЕРСИЙ:\n")
all_ok = True
for name, req_version in required.items():
    if name in installed:
        inst_version = installed[name]
        if req_version == inst_version:
            print(f"✅ {name:30} {inst_version:15} (совпадает)")
        else:
            print(f"⚠️ {name:30} {inst_version:15} (требуется {req_version})")
            all_ok = False
    else:
        print(f"❌ {name:30} не установлен")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ВСЕ ПАКЕТЫ СОВПАДАЮТ!")
else:
    print("⚠️ ЕСТЬ РАСХОЖДЕНИЯ - запустите update_requirements.sh")
print("=" * 60)
