# Original Pocket Tasks contract

This is an original controlled teaching project, not a reimplementation of an external product.

A blank task submission shows `Enter a task.` and leaves the list empty. Saving `Read a chapter` adds that exact task, clears the input and error, and survives a reload. The Save task button is visible at 390 x 700 and 960 x 640 CSS pixels. Blank-state appearance matches the frozen original reference screenshots under the same browser, operating system, fonts, scale, and viewport.

The narrow baseline checks only a successful add, without reload. Enhanced coverage adds blank feedback, save/reload, desktop pixels, and mobile pixels. Each candidate starts with a fresh browser context. The reference and manifests freeze before candidate execution.

Variants deliberately seed known faults: `mobile` hides the button on mobile; `persistence` omits storage writes; `feedback` omits blank-input feedback; `buggy` combines all three; `fixed` follows the original design. These mutations demonstrate detection sensitivity, not independent discovery or complete real-world coverage. Rendering baselines are generated from the known original design, so this trial does not independently establish that the reference itself is correct.
