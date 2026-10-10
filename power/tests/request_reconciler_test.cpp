// SPDX-License-Identifier: Apache-2.0
#include "../request_reconciler.hpp"
#include <cassert>
#include <cstdio>
#include <stdexcept>
using namespace op6::power;

int main() {
  RequestReconciler p;
  auto start = p.MakePlan({{Resource::BigMin, 1209600}, {Resource::GpuMin, 414000000}});
  assert(start.revision == 0 && start.changes.size() == 2);
  assert(start.changes[0].kind == DeltaKind::Set);
  assert(p.Acknowledge(start, true));
  assert(p.Revision() == 1);
  assert(p.LastCommitted().size() == 2);

  auto noop = p.MakePlan({{Resource::BigMin, 1209600}, {Resource::GpuMin, 414000000}});
  assert(noop.changes.empty());
  assert(p.Acknowledge(noop, true));

  // Ending the rendering mode MUST produce an explicit release.
  auto release = p.MakePlan({{Resource::BigMin, 1209600}});
  assert(release.changes.size() == 1);
  assert(release.changes[0].kind == DeltaKind::Release);
  assert(release.changes[0].resource == Resource::GpuMin);
  assert(p.Acknowledge(release, true));

  auto update = p.MakePlan({{Resource::BigMin, 1459200}});
  assert(update.changes.size() == 1 && update.changes[0].kind == DeltaKind::Set);
  assert(update.changes[0].value == 1459200);
  assert(p.Acknowledge(update, true));
  assert(!p.Acknowledge(update, true)); // a stale plan cannot be double-applied

  auto empty = p.MakePlan({});
  assert(empty.changes.size() == 1);
  assert(empty.changes[0].kind == DeltaKind::Release);
  assert(p.Acknowledge(empty, true));
  assert(p.LastCommitted().empty());

  // On partial backend failure, refuse all future plans until verified reset.
  auto failed = p.MakePlan({{Resource::GpuMax, 596000000}});
  assert(!p.Acknowledge(failed, false));
  assert(p.NeedsRecovery());
  bool thrown = false;
  try { (void)p.MakePlan({}); } catch (const std::logic_error&) { thrown = true; }
  assert(thrown);
  assert(!p.Acknowledge(failed, true));
  p.MarkBackendRecovered(); // test simulates proof from a future backend.
  assert(!p.NeedsRecovery() && p.LastCommitted().empty());
  assert(p.MakePlan({}).changes.empty());

  thrown = false;
  try { (void)p.MakePlan({{Resource::GpuMin, -1}}); }
  catch (const std::invalid_argument&) { thrown = true; }
  assert(thrown);
  std::puts("PASS: request delta set/update/release, idempotence, stale generation, recovery");
}
