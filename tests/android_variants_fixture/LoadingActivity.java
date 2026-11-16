package org.swiftest.variantsfixture;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.IOException;
import java.io.InputStream;

/** A local screen with an animated indicator and a controlled change of background. */
public class LoadingActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showLoadingScreen();
    }

    @Override protected void onNewIntent(android.content.Intent intent) {
        super.onNewIntent(intent);
        showLoadingScreen();
    }

    private void showLoadingScreen() {
        FrameLayout page = new FrameLayout(this);
        page.setBackgroundColor(Color.rgb(32, 46, 64));
        ProgressBar spinner = new ProgressBar(this);
        page.addView(spinner, new FrameLayout.LayoutParams(48, 48, Gravity.TOP | Gravity.CENTER_HORIZONTAL));

        ImageView start = new ImageView(this);
        try (InputStream stream = getAssets().open("start.png")) {
            Bitmap icon = BitmapFactory.decodeStream(stream);
            start.setImageBitmap(icon);
            page.addView(start, new FrameLayout.LayoutParams(icon.getWidth(), icon.getHeight(), Gravity.CENTER));
        } catch (IOException e) {
            throw new IllegalStateException("Missing fixture image", e);
        }
        start.setContentDescription("Start loading");
        start.setOnClickListener(v -> {
            start.setVisibility(android.view.View.INVISIBLE);
            page.postDelayed(() -> {
                page.removeAllViews();
                page.setBackgroundColor(Color.rgb(200, 230, 210));
                TextView ready = new TextView(this);
                ready.setText("Ready");
                ready.setGravity(Gravity.CENTER);
                page.addView(ready);
            }, 1200);
        });
        setContentView(page);
    }
}
