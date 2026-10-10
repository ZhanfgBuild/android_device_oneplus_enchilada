// SPDX-License-Identifier: Apache-2.0
// Pure planning, NEVER applies sysfs or libperfmgr requests.
#pragma once
#include "policy_engine.hpp"
#include <cstdint>
#include <map>
#include <stdexcept>
#include <vector>

namespace op6::power {
enum class DeltaKind { Set, Release };
struct Delta {
  Resource resource;
  DeltaKind kind;
  int64_t value; // ignored for Release (defined as 0)
};
struct DeltaPlan {
  uint64_t revision;
  Targets next;
  std::vector<Delta> changes;
};

class RequestReconciler final {
 public:
  DeltaPlan MakePlan(Targets requested) const {
    if (recovery_required_)
      throw std::logic_error("backend state unknown; release/restore before resuming");
    for (const auto& [resource, value] : requested) {
      if (resource < Resource::LittleMin || resource > Resource::GpuMax || value < 0)
        throw std::invalid_argument("invalid performance resource request");
    }
    DeltaPlan plan{revision_, std::move(requested), {}};
    for (const auto& [resource, value] : committed_) {
      const auto target = plan.next.find(resource);
      if (target == plan.next.end())
        plan.changes.push_back({resource, DeltaKind::Release, 0});
    }
    for (const auto& [resource, value] : plan.next) {
      const auto old = committed_.find(resource);
      if (old == committed_.end() || old->second != value)
        plan.changes.push_back({resource, DeltaKind::Set, value});
    }
    return plan;
  }

  // Call this ONLY after a backend fully and atomically applies the whole plan.
  // A failed/partial apply requires explicit backend rollback/restore, NOT a
  // speculative commit against stale sysfs state.
  bool Acknowledge(const DeltaPlan& plan, bool all_applied) {
    if (recovery_required_ || plan.revision != revision_) return false;
    if (!all_applied) {
      recovery_required_ = true;
      return false;
    }
    committed_ = plan.next;
    ++revision_;
    return true;
  }

  bool NeedsRecovery() const noexcept { return recovery_required_; }
  uint64_t Revision() const noexcept { return revision_; }
  const Targets& LastCommitted() const noexcept { return committed_; }

  // The caller MUST prove all backend-held resource requests were released
  // or restored before invoking. No actual release is done by this method.
  void MarkBackendRecovered() noexcept {
    committed_.clear();
    ++revision_;
    recovery_required_ = false;
  }

 private:
  Targets committed_;
  uint64_t revision_ = 0;
  bool recovery_required_ = false;
};
} // namespace op6::power
