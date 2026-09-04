from integrations.razorpay_client import RazorpayClient

class FakeClient(RazorpayClient):
    def __init__(self):
        self.pages = {
            0: {"items": [{"id": "p1"}, {"id": "p2"}]},
            2: {"items": [{"id": "p3"}]},
        }
    def fetch_payments(self, count=100, skip=0):
        return self.pages.get(skip, {"items": []})

def test_fetch_all_payments_paginates():
    c=FakeClient()
    assert [x["id"] for x in c.fetch_all_payments(page_size=2)] == ["p1","p2","p3"]
