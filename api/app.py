
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from db.database import init_db, get_conn
from db.repository import list_cases, get_case, list_case_links, list_case_exceptions
from api.webhooks import router as webhook_router
from api.models import ReviewResolution
from db.repository import resolve_case_manually

init_db()

app=FastAPI(
    title="ReconPilot Finance Controller",
    version="0.6.0",
    description="Persistent finance-ops controller for merchant reconciliation."
)

app.include_router(webhook_router)
app.mount("/web", StaticFiles(directory=str(__import__("pathlib").Path(__file__).resolve().parents[1] / "web")), name="web")

@app.get("/health")
def health():
    return {"status":"ok","service":"reconpilot","version":"0.6.0"}

@app.get("/api/v1/overview/{merchant_id}")
def overview(merchant_id: str):
    conn=get_conn()
    counts={}
    counts["financial_records"]=conn.execute(
        "SELECT COUNT(*) c FROM financial_records WHERE merchant_id=?",(merchant_id,)
    ).fetchone()["c"]
    counts["reconciliation_cases"]=conn.execute(
        "SELECT COUNT(*) c FROM reconciliation_cases WHERE merchant_id=?",(merchant_id,)
    ).fetchone()["c"]
    counts["exceptions"]=conn.execute(
        """SELECT COUNT(*) c FROM exceptions e
           JOIN reconciliation_cases c ON c.case_id=e.case_id
           WHERE c.merchant_id=?""",(merchant_id,)
    ).fetchone()["c"]
    counts["audit_events"]=conn.execute(
        "SELECT COUNT(*) c FROM audit_events WHERE merchant_id=?",(merchant_id,)
    ).fetchone()["c"]
    counts["webhook_events"]=conn.execute(
        "SELECT COUNT(*) c FROM webhook_events WHERE merchant_id=?",(merchant_id,)
    ).fetchone()["c"]
    by_source=conn.execute("""
        SELECT source,COUNT(*) c FROM financial_records
        WHERE merchant_id=? GROUP BY source ORDER BY c DESC
    """,(merchant_id,)).fetchall()
    statuses=conn.execute("""
        SELECT status,COUNT(*) c FROM reconciliation_cases
        WHERE merchant_id=? GROUP BY status
    """,(merchant_id,)).fetchall()
    conn.close()
    return {
        "merchant_id":merchant_id,
        "counts":counts,
        "records_by_source":[dict(r) for r in by_source],
        "case_status":[dict(r) for r in statuses]
    }

@app.get("/api/v1/cases/{merchant_id}")
def cases(merchant_id:str,status:str|None=None):
    return {"items":list_cases(merchant_id,status)}

@app.get("/api/v1/cases/detail/{case_id}")
def case_detail(case_id:str):
    c=get_case(case_id)
    if not c: raise HTTPException(status_code=404,detail="Case not found")
    candidates=[]
    if c.get("case_type")=="invoice_to_payment" and c.get("status") in {"REVIEW","UNRESOLVED"}:
        conn=get_conn()
        inv=conn.execute("SELECT * FROM financial_records WHERE record_id=?",(c.get("primary_record_id"),)).fetchone()
        if inv:
            candidates=conn.execute("""
                SELECT source_record_id,amount,event_date,customer_name,reference
                FROM financial_records
                WHERE merchant_id=? AND source='payment' AND record_type='payment'
                  AND (amount=? OR reference LIKE '%' || ? || '%' OR customer_name=?)
                ORDER BY CASE WHEN amount=? THEN 0 ELSE 1 END, event_date
                LIMIT 8
            """,(c.get("merchant_id"),inv["amount"],inv["source_record_id"],inv["customer_name"],inv["amount"])).fetchall()
        conn.close()
    return {"case":c,"links":list_case_links(case_id),"exceptions":list_case_exceptions(case_id),
            "review_candidates":[dict(r) for r in candidates]}


@app.post("/api/v1/cases/{case_id}/resolve")
def resolve_case(case_id: str, req: ReviewResolution):
    try:
        return {"case": resolve_case_manually(case_id, req.action, req.payment_id, req.note, req.actor)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/exceptions/{merchant_id}")
def exceptions(merchant_id:str):
    conn=get_conn()
    rows=conn.execute("""
    SELECT e.exception_id,e.case_id,e.severity,e.reason,e.status,e.created_at,
           c.case_type,c.confidence,c.primary_record_id,c.matched_record_id,c.decision_source
    FROM exceptions e
    JOIN reconciliation_cases c ON c.case_id=e.case_id
    WHERE c.merchant_id=?
    ORDER BY e.created_at DESC
    """,(merchant_id,)).fetchall()
    conn.close()
    return {"items":[dict(r) for r in rows]}


@app.get("/api/v1/dashboard/{merchant_id}")
def dashboard(merchant_id: str):
    conn = get_conn()
    record_total = conn.execute(
        "SELECT COUNT(*) c FROM financial_records WHERE merchant_id=?", (merchant_id,)
    ).fetchone()["c"]
    counts = {
        "financial_records": record_total,
        "reconciliation_cases": conn.execute(
            "SELECT COUNT(*) c FROM reconciliation_cases WHERE merchant_id=?", (merchant_id,)
        ).fetchone()["c"],
        "exceptions": conn.execute("""
            SELECT COUNT(*) c
            FROM exceptions e
            JOIN reconciliation_cases c ON c.case_id=e.case_id
            WHERE c.merchant_id=?
        """, (merchant_id,)).fetchone()["c"],
        "audit_events": conn.execute(
            "SELECT COUNT(*) c FROM audit_events WHERE merchant_id=?", (merchant_id,)
        ).fetchone()["c"],
        "webhook_events": conn.execute(
            "SELECT COUNT(*) c FROM webhook_events WHERE merchant_id=?", (merchant_id,)
        ).fetchone()["c"],
    }
    sources = conn.execute("""
        SELECT source, COUNT(*) c
        FROM financial_records WHERE merchant_id=?
        GROUP BY source ORDER BY c DESC
    """, (merchant_id,)).fetchall()
    case_status = conn.execute("""
        SELECT status, COUNT(*) c
        FROM reconciliation_cases WHERE merchant_id=?
        GROUP BY status
    """, (merchant_id,)).fetchall()
    recent = conn.execute("""
        SELECT event_type, actor, payload_json, created_at
        FROM audit_events WHERE merchant_id=?
        ORDER BY created_at DESC LIMIT 12
    """, (merchant_id,)).fetchall()
    conn.close()
    return {
        "record_total": counts["financial_records"],
        "counts": counts,
        "sources": [dict(r) for r in sources],
        "case_status": [dict(r) for r in case_status],
        "recent_activity": [dict(r) for r in recent],
    }

@app.get("/", include_in_schema=False)
def root():
    return FileResponse(__import__("pathlib").Path(__file__).resolve().parents[1] / "web" / "index.html")
