# Android Blender

Touch-input fixes for Android Blender, starting with the **Android Touch Transform Fix v1.1.0** add-on.

Finger-driven transforms can jump to an unrelated position or confirm as soon as you touch the screen. This add-on keeps movement relative to the first touch and confirms when you lift your finger. It also repairs the handler ordering that allowed **Edge menu → Edge Slide** to bypass the fix.

This repository currently contains a Python add-on for [Wanderson Magalhães's Android Blender build](https://github.com/Wanderson-Magalhaes/blender_for_android). It does not contain a replacement APK or the full Blender source tree.

## Compatibility

| Requirement | Supported value |
| --- | --- |
| Platform | Android, 64-bit pointers |
| Blender build hash | `7dd3aa7e0e95` |
| Tested app version | 5.3.0 Beta (S24 Ultra) |
| Tested device | Samsung SM_F971B |

The add-on deliberately refuses to register on other builds. Check your build in Blender's Python Console:

```python
print(bpy.app.version_string, bpy.app.build_hash)
```

**This is an experimental, build-specific patch.** It uses `ctypes` to modify part of Blender's native input event structure. It validates the build and event layout before writing, but those checks do not make it portable to other binaries. Save your work before installing and do not bypass the build guard after updating Blender.

## Install

1. Download [`android_touch_transform.py`](https://raw.githubusercontent.com/drshaggy/android-blender/main/android_touch_transform.py).
2. In Blender, open **Edit → Preferences → Add-ons** and use **Install from Disk** from the menu to select the downloaded Python file.
3. Enable **Android Touch Transform Fix**, then save preferences.
4. Restart Blender and test on a disposable mesh.

No special launch flags are required. Disable the add-on in Preferences and save preferences to turn it off.

## Use

- Start a move, scale, extrusion, or edge slide, then touch and drag in the viewport.
- The first contact establishes the touch origin; subsequent motion controls the transform.
- Lift your finger to confirm.
- For Loop Cut and Slide, select the cut first, then use the following drag to slide it.
- Keyboard input, including numeric values, axis constraints, and Escape cancellation, passes through.

Navigation gestures remain as configured by the Android build. This version does not add on-screen axis buttons.

## Verification

The fix was exercised on the physical test device using ADB-injected single-finger events, including checks after restarting the app. See [`verification/`](verification/) for recorded test-mesh coordinates and operator states, and the distinction between v1.0.0 and v1.1.0 checks.

- Scale: initial contact stays at 1; outward motion reaches about 1.133 and reversing the drag reaches about 0.916.
- Grab and extrusion: later movement continues to update geometry instead of confirming at first contact.
- Loop Cut and Slide: new vertices move in both directions before confirmation.
- Edge menu → Edge Slide, v1.1.0 after restart: the test loop moves from 0 to approximately +0.514, +0.857, then −0.514, remaining active until finger release.
- Numeric input and Escape cancellation were checked on the device.

These are recorded device checks, not an automated cross-device test suite. Physical stylus input and multi-finger interaction with an active transform have not been validated.

## How it works

A priority modal handler rebases pointer coordinates during an existing transform, consumes the touch press that would otherwise confirm it, and converts finger release into an Enter press. The add-on does not directly edit mesh geometry.

Blender may place operators launched by popup menus ahead of priority handlers. A 25 ms timer detects that ordering and re-arms the touch handler through Blender's operator API. Per-window tokens retire the previous handler. Scripted input immediately after a menu invocation must allow time for that timer to run; the repair is not synchronous.

The event-layout guard checks native fields against Blender's Python event properties before any write. An exception disables the patch. Native input handling would be the appropriate place for a general solution across Blender versions.

## Credits and license

- Android Blender port: [Wanderson Magalhães and contributors](https://github.com/Wanderson-Magalhaes/blender_for_android).
- Blender: [Blender Foundation and contributors](https://www.blender.org/).
- This add-on: developed and tested by Connor with Codex.

Add-on source is licensed under **GPL-3.0-or-later**. See [LICENSE](LICENSE).
