# Recorded device checks

These snapshots were captured from disposable test scenes on 26 October 2026 using ADB-injected touch events on a Samsung SM_F971B, running Android Blender build `7dd3aa7e0e95`.

| File | Add-on version | Coverage |
| --- | --- | --- |
| `transforms-v1.0.0.json` | 1.0.0 | Scale, numeric entry, constrained numeric move, grab cancellation, after restart |
| `loopcut-v1.0.0.json` | 1.0.0 | Full loop-cut macro, slide in both directions, release confirmation |
| `edge-menu-before-v1.0.0.json` | 1.0.0 | Reproduction of menu-started slide prematurely confirming |
| `edge-menu-v1.1.0.json` | 1.1.0 | Menu-started slide moving both ways and confirming on release, after restart |
| `back-v1.2.0.json` | 1.2.0 | Idle Undo, active move/Knife cancellation, menu/keyboard dismissal, physical Escape |
| `back-extra-v1.2.0.json` | 1.2.0 | Held Back, keyboard dismissal during a transform, Timeline Escape unchanged |
| `back-restart-v1.2.0.json` | 1.2.0 | Automatic registration and idle Back Undo after app restart |
| `back-touch-v1.2.0.json` | 1.2.0 | Touch-driven grab continues updating; Back cancels it |
| `installed-build.json` | 1.2.0 | Version and SHA-256 of the enabled source on the device |

The snapshots retain test-mesh geometry and modal operator names. Session IDs, timestamps, and local installation/model paths are omitted. Files are historical observations, not executable tests. An older retired touch handler can remain in the modal operator list during the slide; its per-window token prevents it from processing input, and it exits when it next receives an event.

For a manual regression check, use a saved disposable mesh: test initial contact, several moves in the same drag, reversing direction, release confirmation, keyboard numeric input, and Escape cancellation. Test Edge Slide through the Edge menu separately from the G/G shortcut and Loop Cut and Slide.
