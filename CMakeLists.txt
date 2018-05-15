cmake_minimum_required(VERSION 3.5)

project(SlicerSpectroscopy)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/PrinterInteractor")
set(EXTENSION_CATEGORY "SlicerSpectroscopy")
set(EXTENSION_CONTRIBUTORS "Laura Connolly (PerkLab (Queen's University)), Mark Asselin (PerkLab (Queen's University))")
set(EXTENSION_DESCRIPTION "This is an extension that uses Plus to communicate with the Monoprice Mini V2 3D Printer")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/PrinterInteractor.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/PrinterInteractor/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(PrinterInteractor)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
