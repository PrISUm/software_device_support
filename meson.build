project('Device Support', 'c')

# Exported variables:
# device_support: A dict of family name to a dependency declaration
#   which can be used for including the device support headers or locating the SVD files for debugging.

sam_support = {}
foreach sam : ['samc21', 'samd21a', 'samd21b', 'samd21c', 'samd21d']
  sam_support += {
    sam: declare_dependency(
      compile_args: [ 
        '-I' + (meson.current_source_dir() / sam / 'include'),
        '-I' + (meson.current_source_dir() / 'CMSIS' / 'Core' / 'Include'),
        '-DDONT_USE_CMSIS_INIT'
      ],
      variables: {
        'svd_dir': meson.current_source_dir() / sam / 'svd'
      }
    )
  }
endforeach



device_support = {
  'avr': declare_dependency(
    compile_args: '-I' + (meson.current_source_dir() / 'avr' / 'include')
  ),
} + sam_support