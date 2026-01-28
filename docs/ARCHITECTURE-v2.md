# 🏛️ Distributed Edge Intelligence (Architecture v2.0)
**Status:** DRAFT (Research Phase)
**Target:** Raspberry Pi 5 + AI HAT+ 2 (Hailo-10H)

---

## 1. The Strategic Pivot
**v1.0 (Current):** Centralized Processing (Laptop). High latency, single failure point.
**v2.0 (Target):** Distributed Edge Intelligence. Low latency, swarm capability.

---

## 2. Hardware Profiles (Select Your Mission)

### 🟢 Profile A: "The Scout" (Telemetry Only)
* **Best For:** Long-duration surveillance, Remote ID monitoring, ADSB tracking.
* **Video:** NONE (or low-res stream only).
* **Hardware Spec:**
    * **SBC:** **Raspberry Pi 5 (8GB)**.
    * **Accelerator:** AI HAT+ 2 (Hailo-10H).
    * **Storage:** 256GB NVMe (Telemetry logs are small).
* **Why 8GB?**
    * The OS takes ~1GB.
    * The Llama 3.1 Pilot (INT4) lives entirely on the **Hailo's 8GB RAM**.
    * The Vector DB (RAG) for text-only logs fits easily in ~2GB host RAM.
    * **Result:** You have ~5GB free RAM. 16GB is wasted money/power here.

### 🔴 Profile B: "The Sentinel" (Full Fusion)
* **Best For:** Threat detection, forensic evidence capture, visual tracking.
* **Video:** 4K@60fps Ring Buffer (60s pre-event).
* **Hardware Spec:**
    * **SBC:** **Raspberry Pi 5 (16GB)**.
    * **Accelerator:** AI HAT+ 2 (Hailo-10H).
    * **Storage:** 1TB+ NVMe (Video eats space).
* **Why 16GB?**
    * A 60-second 4K raw buffer consumes ~8-10GB of RAM.
    * Swapping this to disk (even NVMe) kills the SSD life and slows response.
    * **Result:** 16GB is mandatory to hold the video evidence in RAM until an "Incident" triggers a write.

---

## 3. The "Split-Brain" Memory Architecture
The AI HAT+ 2 introduces a dedicated memory pool, changing the resource math.

| Resource | "The Scout" (8GB Host) | "The Sentinel" (16GB Host) |
| :--- | :--- | :--- |
| **Generative AI** | Offloaded to Hailo (8GB dedicated) | Offloaded to Hailo (8GB dedicated) |
| **Vision AI** | Offloaded to Hailo | Offloaded to Hailo |
| **Host RAM Usage** | ~2GB (OS + DB) | ~12GB (OS + DB + **Video Buffers**) |
| **Power Draw** | ~5W (Idle) | ~7W (Idle - maintaining RAM) |

---

## 4. Migration Recommendation
**Start with Profile B (16GB).**
* **Reason:** The cost difference (~) is negligible compared to the flexibility. You can always run a "Scout" mission on a "Sentinel" box, but you can't run a video mission on a memory-starved box.
* **DevOps Benefit:** 16GB allows you to compile models and run Docker containers directly on the device without cross-compiling on other computers.

---

## 5. References
* [Introducing the Raspberry Pi AI HAT+ 2: Generative AI on Raspberry Pi 5](https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/)

---

## 6. The PCIe Reality (AI vs. Storage)
**Critical Constraint:** The Raspberry Pi 5 possesses only **one** PCIe user port. The **AI HAT+ 2** consumes this port entirely. Consequently, you cannot utilize a standard NVMe HAT and the AI HAT+ 2 simultaneously without specialized hardware.

### Solution Options for v2.0
#### Option A: USB 3.1 Boot (Recommended)
* **Configuration:** AI HAT+ 2 (PCIe) + High-Speed USB 3.1 Gen 1 SSD (e.g., Samsung T7 or M.2 SATA-to-USB adapter).
* **Pros:** Simplest implementation, high reliability, preserves 100% of AI bandwidth.
* **Cons:** USB 3.0 latency is slightly higher than NVMe (negligible impact on this architecture provided the Video Ring Buffer stays in RAM).

#### Option B: PCIe Packet Switch (Advanced)
* **Configuration:** Use a PCIe Packet Switch (e.g., *Pineboards HatBRICK! Commander*) to split the single lane into two.
* **Pros:** Enables simultaneous AI HAT+ 2 and NVMe usage.
* **Cons:** Significantly increases physical stack height (bulky), requires custom enclosure, and adds hardware cost. Bandwidth is shared (Gen 2 x1) between AI and Storage.
