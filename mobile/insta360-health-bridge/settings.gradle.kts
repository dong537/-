pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://oss.sonatype.org/content/repositories/snapshots") }
        maven { url = uri("https://jitpack.io") }
        maven {
            url = uri("https://androidsdk.insta360.com/repository/maven-public/")
            isAllowInsecureProtocol = true
            credentials {
                username = providers.gradleProperty("INSTA360_MAVEN_USERNAME")
                    .orElse(providers.environmentVariable("INSTA360_MAVEN_USERNAME"))
                    .orNull
                    .orEmpty()
                password = providers.gradleProperty("INSTA360_MAVEN_PASSWORD")
                    .orElse(providers.environmentVariable("INSTA360_MAVEN_PASSWORD"))
                    .orNull
                    .orEmpty()
            }
        }
    }
}

rootProject.name = "Insta360HealthBridge"
include(":app")
