# Xlibe gaps for the UXP GTK3/X11 backend on Haiku

## Blocker: Haiku's GTK3 does not use Xlibe

Checked in the build VM (Haiku R1/beta6, gtk3_devel 3.24.52):

- HaikuPorts' gtk3 recipe builds with `-Dx11_backend=false -Dwayland_backend=true`.
  `pkg-config --variable=targets gdk-3.0` prints `wayland`. There is no `gdk/gdkx.h`
  and no `gdk-x11-3.0.pc`. `libgdk-3.so.0` links libwayland-client, not libX11.
- The installed `cairo` has no Xlib surface (no libX11 in NEEDED). `xcairo` (with Xlib
  surfaces) is in the repo, but it conflicts with `cairo`.
- UXP's gtk3 widget code needs GDK's X11 backend (`gdk_x11_*` everywhere, MOZ_X11
  hard-on: `--without-x is not supported` in toolkit/moz.configure).

So "cairo-gtk3 through Xlibe" can't be built against the stock packages. Ways forward
(the lead has to choose):
1. Build GTK3 locally with the X11 backend against Xlibe. GTK 3.24 needs
   x11, xext, xrender, xi and xrandr >= 1.2.99. Xlibe provides only x11 and xext,
   so xrender, xi and xrandr would need stub libraries/.pc files. Swap cairo for xcairo.
2. Teach UXP's GTK3 widget to run on GDK Wayland (UXP has no Wayland code. That is a big port).
3. Skip to the native widget/haiku (step 2 of the plan).

## What Xlibe provides (xlibe_devel, x11.pc 1.6.12)

libX11 (most of core Xlib, incl. XKB basics and Xrm) and libXext (XShmPutImage/
XShmGetImage as XPutImage/XGetSubImage wrappers, plus shape and sync stubs).
Headers: X11/*, X11/extensions/{XShm,shape,sync}.h. xorgproto (render.h,
renderproto.h, ...) is installed. There is no GL/glx.h (Mesa provides GL, EGL and OSMesa).
`XShmQueryExtension`/`XShmAttach`/`XShmCreateImage` are declared but **not exported**.
`XQueryExtension` is a stub that returns 0, and `XextAddDisplay` is missing.

## Gaps and what was done (branch haiku-widget, commit 69653cf669)

| X11 API | Used by | Action on Haiku |
|---|---|---|
| Xrender (libXrender) | in-tree cairo xlib backend, gfxXlibSurface, DrawTargetCairo, gfxXlibNativeRenderer, ShadowLayerUtilsX11, nsWindow, WindowSurfaceXRender | Stub: widget/x11/haiku exports libXrender 0.9.10's Xrender.h and links no-op stubs (extension absent, formats NULL). Cairo and gfx already handle a server without RENDER. No `-lXrender`. |
| xcb, xcb-shm, X11-xcb (MIT-SHM) | widget/nsShmImage, WindowSurfaceX11SHM | Guarded: MOZ_HAVE_SHMIMAGE is off on Haiku, so drawing goes through WindowSurfaceX11Image (XPutImage). configure skips the checks. |
| XShm (Xext) | nsWindow.cpp (header only), mozgtk (NPAPI only) | No action: the header exists and the functions aren't called. |
| GLX | gfx/gl GLContextProviderGLX/X11, SharedSurfaceGLX, GL_PROVIDER_GLX users | Guarded: no GLX sources, GL_PROVIDER_GLX undefined, and GLContextProviderNull is the default. That means basic (software) compositing and no WebGL. |
| Xt, ICE, SM | widget/gtkxtbin (NPAPI), toolkit/xre/nsNativeAppSupportUnix (session mgmt) | configure skips the checks. gtkxtbin is only built with NPAPI (disabled). **nsNativeAppSupportUnix.cpp still includes ICE/SM. Toolkit must guard it (MOZ_X11 && !XP_HAIKU).** |
| Xss (screensaver) | nsIdleServiceGTK | No action: it's dlopen'd at runtime and skipped in configure. |
| XComposite, XDamage, XFixes, XInput2, XRandR, XSync | not called directly by UXP | None needed. |
| XQueryExtension (stub returning 0) | gfxPlatformGtk/X11 checks | Code treats extensions as absent. That's fine. |
