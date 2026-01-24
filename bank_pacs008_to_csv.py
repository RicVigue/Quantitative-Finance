# -*- coding: utf-8 -*-
"""
bank_pacs008_to_csv.py
Uso:
    python bank_pacs008_to_csv.py pacs008.xml salida.csv [credit_posting_ts]
Convierte pacs.008 (entrante) a un CSV de conciliación para el cliente.
"""
import sys, csv
from xml.etree import ElementTree as ET
from datetime import datetime

NS = {"ns": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}

def _text(e): return (e.text or "").strip() if e is not None else ""

def find_first(elem, paths):
    for p in paths:
        x = elem.find(p, NS)
        if x is not None and _text(x):
            return _text(x)
    return ""

def main():
    if len(sys.argv) < 3:
        print("Uso: python bank_pacs008_to_csv.py pacs008.xml salida.csv [credit_posting_ts]")
        sys.exit(1)
    xml_path, out_csv = sys.argv[1], sys.argv[2]
    credit_ts = sys.argv[3] if len(sys.argv) >= 4 else datetime.utcnow().isoformat()

    tree = ET.parse(xml_path)
    root = tree.getroot()

    grp_hdr = root.find(".//ns:GrpHdr", NS)
    msg_id = _text(grp_hdr.find("ns:MsgId", NS)) if grp_hdr is not None else ""
    cre_dt_tm = _text(grp_hdr.find("ns:CreDtTm", NS)) if grp_hdr is not None else ""

    rows = []
    for i, tx in enumerate(root.findall(".//ns:CdtTrfTxInf", NS), start=1):
        instr_id = _text(tx.find("ns:PmtId/ns:InstrId", NS))
        end2end = _text(tx.find("ns:PmtId/ns:EndToEndId", NS))
        tx_id = _text(tx.find("ns:PmtId/ns:TxId", NS))
        amt_el = tx.find("ns:IntrBkSttlmAmt", NS)
        amount = _text(amt_el) if amt_el is not None else ""
        ccy = amt_el.get("Ccy") if amt_el is not None else ""
        chrg_br = _text(tx.find("ns:ChrgBr", NS))
        uetr = ""
        uetr_el = tx.find(".//ns:UETR", NS)
        if uetr_el is not None and _text(uetr_el):
            uetr = _text(uetr_el)

        dbtr_name = _text(tx.find("ns:Dbtr/ns:Nm", NS))
        dbtr_iban = find_first(tx, ["ns:DbtrAcct/ns:Id/ns:IBAN", "ns:DbtrAcct/ns:Id/ns:Othr/ns:Id"])
        cdtr_name = _text(tx.find("ns:Cdtr/ns:Nm", NS))
        cdtr_iban = find_first(tx, ["ns:CdtrAcct/ns:Id/ns:IBAN", "ns:CdtrAcct/ns:Id/ns:Othr/ns:Id"])
        cdtr_bic = find_first(tx, ["ns:CdtrAgt/ns:FinInstnId/ns:BICFI"])
        purp = _text(tx.find("ns:Purp/ns:Cd", NS))

        ustrd_list = [ _text(u) for u in tx.findall("ns:RmtInf/ns:Ustrd", NS) if _text(u) ]
        remittance = " | ".join(ustrd_list)

        rows.append({
            "bank_msg_id": msg_id,
            "creation_datetime": cre_dt_tm,
            "transaction_seq": i,
            "instr_id": instr_id,
            "end_to_end_id": end2end,
            "tx_id": tx_id,
            "uetr": uetr,
            "amount": amount,
            "currency": ccy,
            "charges_bearer": chrg_br,
            "debtor_name": dbtr_name,
            "debtor_account": dbtr_iban,
            "creditor_name": cdtr_name,
            "creditor_account": cdtr_iban,
            "creditor_bic": cdtr_bic,
            "purpose_code": purp,
            "remittance_information": remittance,
            "credit_posting_ts": credit_ts  # sello de tiempo de abono al cliente
        })

    # Columnas ordenadas (contrato de datos con el cliente)
    cols = ["bank_msg_id","creation_datetime","transaction_seq",
            "instr_id","end_to_end_id","tx_id","uetr",
            "amount","currency","charges_bearer",
            "debtor_name","debtor_account",
            "creditor_name","creditor_account","creditor_bic","purpose_code",
            "remittance_information","credit_posting_ts"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Generado CSV: {out_csv} ({len(rows)} filas)")

if __name__ == "__main__":
    main()
