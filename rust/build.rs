use bindgen::EnumVariation;
use std::env;
use std::path::PathBuf;

fn main() {
    println!("cargo:rustc-link-lib=libra_dev");
    println!("cargo:rustc-link-search=native=../libra-dev/target/debug/");

    // Tell cargo to invalidate the built crate whenever the wrapper changes
    println!("cargo:rerun-if-changed=../libra-dev/include/data.h");

    // The bindgen::Builder is the main entry point
    // to bindgen, and lets you build up options for
    // the resulting bindings.
    let bindings = bindgen::Builder::default()
        // The input header we would like to generate
        // bindings for.
        .header("../libra-dev/include/data.h")
        // Finish the builder and generate the bindings.
        .array_pointers_in_arguments(true)
        .derive_default(true)
        .derive_eq(true)
        .default_enum_style(EnumVariation::Rust {
            non_exhaustive: false,
        })
        .generate()
        // Unwrap the Result and panic on failure.
        .expect("Unable to generate bindings");

    // Write the bindings to the $OUT_DIR/bindings.rs file.
    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
