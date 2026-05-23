package com.panorama.insta360healthbridge

import android.app.Application
import com.arashivision.sdkcamera.InstaCameraSDK
import com.arashivision.sdkmedia.InstaMediaSDK

class Insta360HealthBridgeApp : Application() {
    override fun onCreate() {
        super.onCreate()
        InstaCameraSDK.init(this)
        InstaMediaSDK.init(this)
    }
}
