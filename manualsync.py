import pyodbc
from supabase import create_client, Client
import argparse
import os

# --- 1. Connections ---

MSSQL_CONN = (
    "DRIVER={SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=Marcoco_V4;"
    "Trusted_Connection=yes;"
)

SUPABASE_URL = "https://blkqqjphteoupdgcsvvd.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. Sync Function ---
def sync_inventory_summary():
    """Calculates the heavy inventory math on MSSQL and syncs the summary to Supabase."""
    print("🔄 Calculating and Syncing Inventory Summary...")
    cursor = pyodbc.connect(MSSQL_CONN).cursor()
    
    query = """
    SELECT 
        I.IRCode + I.IR_IMCode AS item,
        I.IRName + I.IR_IMName AS description,
        CASE WHEN ISNULL(S.qty, 0) - ISNULL(C.qty, 0) < 0 THEN 0 ELSE CAST(ISNULL(S.qty, 0) - ISNULL(C.qty, 0) AS INT) END AS stock,
        CAST(CAST(ISNULL(S.qty, 0) AS INT) AS VARCHAR(20)) + ' - ' + CAST(CAST(ISNULL(C.qty, 0) AS INT) AS VARCHAR(20)) + ' - ' + CAST(CAST(ISNULL(N.qty, 0) AS INT) AS VARCHAR(20)) + ' - ' + CAST(CAST(ISNULL(P.qty, 0) - ISNULL(N.qty, 0) AS INT) AS VARCHAR(20)) AS stk_co_inc_po,
        CAST(ISNULL(S.qty, 0) AS INT) AS stk,
        CAST(ISNULL(C.qty, 0) AS INT) AS co,
        CAST(ISNULL(N.qty, 0) AS INT) AS inc,
        CAST(ISNULL(P.qty, 0) - ISNULL(N.qty, 0) AS INT) AS po,
        CAST(CAST(ROUND(ISNULL(PB.BPBExportP, 0), 0) AS INT) AS VARCHAR(20)) + ' - ' + CAST(CAST(ROUND(ISNULL(PB.BPBLocalP, 0), 0) AS INT) AS VARCHAR(20)) + ' - ' + CAST(CAST(ROUND(ISNULL(PB.BPBExportP2, 0), 0) AS INT) AS VARCHAR(20)) AS abo_display,
        CAST(ROUND(ISNULL(PB.BPBExportP, 0), 0) AS INT) AS price_a,
        CAST(ROUND(ISNULL(PB.BPBLocalP, 0), 0) AS INT) AS price_b,
        CAST(ROUND(ISNULL(PB.BPBExportP2, 0), 0) AS INT) AS price_o,
        PG.IRGCODE AS ir_group,
        SG.IRGCODE AS ir_sub,
        I.IRID AS irid
    FROM Item_raw I
    LEFT JOIN ITEM_RAWGROUP SG ON I.IR_IRGID = SG.IRGID
    LEFT JOIN ITEM_RAWGROUP PG ON SG.IRGPARENT = PG.IRGID
    LEFT JOIN PriceBBase PB ON I.IRID = PB.BPB_IRID
    LEFT JOIN (SELECT stkl_irid, SUM(stkltrxqty) AS qty FROM stockledger WHERE stkl_WHID IN (20) GROUP BY stkl_irid) S ON I.IRID = S.stkl_irid
    LEFT JOIN (SELECT IRID, SUM((ISNULL(codqty,0) - ISNULL(codqtydeliver,0))) AS qty FROM CO_dtl INNER JOIN item_raw ON cod_ib_id = IRID WHERE codstatus NOT IN (2,3) GROUP BY IRID) C ON I.IRID = C.IRID
    LEFT JOIN (SELECT agrndtl_irid, SUM(ISNULL(agrndtl_quan,0)) AS qty FROM agrn_dtl INNER JOIN agrn_hdr ON agrndtl_agrnhdrid = agrnhdrid WHERE AGRNhdrVIStatus <> 2 GROUP BY agrndtl_irid) N ON I.IRID = N.agrndtl_irid
    LEFT JOIN (SELECT POD_IRID, SUM(ISNULL(podqty,0) - ISNULL(podqtydeliver,0)) AS qty FROM po_dtl INNER JOIN po_hdr ON pod_poid = poid WHERE postatus = 1 AND podstatus <> 2 AND podate > '2002-04-01' GROUP BY POD_IRID) P ON I.IRID = P.POD_IRID
    WHERE I.IR_ForSale = 1
    """
    
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    if rows:
        supabase.table("inventory_summary").upsert(rows, on_conflict="irid").execute()
        print(f"✅ Synced {len(rows)} inventory summaries to Supabase.")
    else:
        print("️ No inventory data found.")

# --- 3. Command Line Interface ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="On-Demand MSSQL to Supabase Sync")
    parser.add_argument("task", choices=["summary"], help="Task to execute (currently only 'summary')")
    
    args = parser.parse_args()

    if args.task == "summary":
        sync_inventory_summary()