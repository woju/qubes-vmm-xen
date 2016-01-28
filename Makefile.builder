ifeq ($(PACKAGE_SET),dom0)
  RPM_SPEC_FILES := xen.spec

else ifeq ($(PACKAGE_SET),vm)
  RPM_SPEC_FILES := xen.spec
  ARCH_BUILD_DIRS := archlinux

  ifneq ($(filter $(DISTRIBUTION), debian qubuntu),)
    DEBIAN_BUILD_DIRS := debian
  endif
endif

# vim: filetype=make
