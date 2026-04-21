import Link from "next/link";

const DEMO_CUSTOMERS = [
  { id: "c1", customer_name: "X insurance", status: "In Progress", owner: "Sid", integration_type: "Claims File Feed", go_live_date: "2026-05-15" },
  { id: "c2", customer_name: "Orchid Health", status: "At Risk", owner: "Shuo", integration_type: "API Integration", go_live_date: "2026-05-28" },
  { id: "c3", customer_name: "Pioneer Payer", status: "On Track", owner: "Ravi", integration_type: "SFTP Batch", go_live_date: "2026-06-10" },
  { id: "c4", customer_name: "Harbor Health Plan", status: "On Track", owner: "Ananya", integration_type: "HL7/FHIR", go_live_date: "2026-06-25" },
];

export default function ManageCustomers() {
  return (
    <main className="page">
      <header className="topbar">
        <div className="brand">DAFFODIL</div>
      </header>

      <div className="layout">
        <aside className="sidebar-nav">
          <div className="sidebar-brand">DAFFODIL OPS</div>
          <nav className="nav-list">
            <Link className="nav-item nav-link" href="/">Home</Link>
            <Link className="nav-item nav-link" href="/">Add New Customer</Link>
            <div className="nav-item nav-active">Manage Customers</div>
          </nav>
        </aside>

        <section className="content">
          <h1>Manage Customers</h1>
          <p className="lead">View active implementation workspaces and operational status.</p>

          <section className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Status</th>
                    <th>Owner</th>
                    <th>Integration</th>
                    <th>Go-Live Date</th>
                  </tr>
                </thead>
                <tbody>
                  {DEMO_CUSTOMERS.map((c) => (
                    <tr key={c.id}>
                      <td>{c.customer_name}</td>
                      <td>{c.status}</td>
                      <td>{c.owner}</td>
                      <td>{c.integration_type}</td>
                      <td>{c.go_live_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
