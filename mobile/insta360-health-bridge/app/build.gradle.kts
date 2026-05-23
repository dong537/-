plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.panorama.insta360healthbridge"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.panorama.insta360healthbridge"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    packaging {
        resources {
            excludes += listOf("META-INF/rxjava.properties")
            pickFirsts += listOf("lib/arm64-v8a/libc++_shared.so")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation(libs.insta.camera)
    implementation(libs.insta.media)
}
