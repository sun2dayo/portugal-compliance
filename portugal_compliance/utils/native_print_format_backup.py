"""
Backup/restauro dos Print Formats nativos da ERPNext (Sales Invoice, POS
Invoice, Payment Entry, Delivery Note) antes de lhes injetar os elementos
de compliance fiscal portuguesa (ATCUD, QR Code, hash de assinatura,
texto de certificação). Ver plano: compliance para print formats nativos,
2026-09-02.

Estes 11 registos "Print Format" pertencem aos módulos Accounts/Selling/
Stock da própria ERPNext, não ao nosso módulo - por isso não podem viver
como fixture normal (a fixture "Print Format" deste app está filtrada por
module="Portugal Compliance"). Este backup serve exclusivamente para
permitir uma restauração rápida e segura em caso de erro na injeção.
"""

import json
import os

import frappe

NATIVE_PRINT_FORMATS = [
	"Sales Invoice Standard",
	"Sales Invoice with Item Image",
	"Sales Invoice Return",
	"Sales Auditing Voucher",
	"POS Invoice Standard",
	"POS Invoice with Item Image",
	"Return POS Invoice",
	"POS Invoice",
	"Delivery Note Standard",
	"Delivery Note with Item Image",
	"Bank and Cash Payment Voucher",
]

BACKUP_FIELDS = [
	"name", "doc_type", "module", "standard", "disabled",
	"print_format_type", "print_format_builder", "html", "css",
	"format_data", "raw_printing", "raw_commands",
	"font_size", "margin_top", "margin_bottom", "margin_left", "margin_right",
	"modified",
]

BACKUP_DIR = os.path.join(
	frappe.get_app_path("portugal_compliance"),
	"..", "backups", "native_print_formats",
)


def backup_native_print_formats():
	"""Grava o estado atual (pristine) dos 11 Print Formats nativos num
	ficheiro JSON com data, para restauro rápido em caso de erro. Deve ser
	commitado ao git logo a seguir a correr - é a rede de segurança antes
	de qualquer injeção de compliance."""
	snapshot = []
	missing = []
	for name in NATIVE_PRINT_FORMATS:
		if not frappe.db.exists("Print Format", name):
			missing.append(name)
			continue
		doc = frappe.db.get_value("Print Format", name, BACKUP_FIELDS, as_dict=True)
		snapshot.append(doc)

	if missing:
		frappe.logger().warning(
			f"backup_native_print_formats: Print Formats nao encontrados (ignorados): {missing}"
		)

	os.makedirs(BACKUP_DIR, exist_ok=True)
	date_str = frappe.utils.nowdate()
	path = os.path.join(BACKUP_DIR, f"pristine_{date_str}.json")
	with open(path, "w", encoding="utf-8") as f:
		json.dump(snapshot, f, indent=1, sort_keys=True, ensure_ascii=False, default=str)

	frappe.logger().info(f"backup_native_print_formats: {len(snapshot)} formatos gravados em {path}")
	return path, len(snapshot), missing


@frappe.whitelist()
def restore_native_print_formats(names=None, snapshot_path=None):
	"""Restaura os Print Formats nativos a partir do backup mais recente
	(ou de um snapshot_path especifico). names: lista opcional de nomes a
	restaurar (default: todos os presentes no snapshot)."""
	if isinstance(names, str):
		names = json.loads(names) if names.startswith("[") else [names]

	if not snapshot_path:
		if not os.path.isdir(BACKUP_DIR):
			frappe.throw("Nenhum backup encontrado em " + BACKUP_DIR)
		snapshots = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith("pristine_") and f.endswith(".json"))
		if not snapshots:
			frappe.throw("Nenhum ficheiro de backup encontrado em " + BACKUP_DIR)
		snapshot_path = os.path.join(BACKUP_DIR, snapshots[-1])

	with open(snapshot_path, encoding="utf-8") as f:
		snapshot = json.load(f)

	restored = []
	for record in snapshot:
		if names and record["name"] not in names:
			continue
		if not frappe.db.exists("Print Format", record["name"]):
			continue
		doc = frappe.get_doc("Print Format", record["name"])
		for field in BACKUP_FIELDS:
			if field in ("name", "modified"):
				continue
			doc.set(field, record.get(field))
		doc.save(ignore_permissions=True)
		restored.append(record["name"])

	frappe.db.commit()
	frappe.logger().info(f"restore_native_print_formats: restaurados a partir de {snapshot_path}: {restored}")
	return {"snapshot": snapshot_path, "restored": restored}
