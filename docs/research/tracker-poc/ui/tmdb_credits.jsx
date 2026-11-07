import React from "react";

// TMDB's unmodified logo is requested without the current film URL as referrer.
const logo = "https://www.themoviedb.org/assets/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg";

export function TmdbCredits() {
  return <section><h4>Credits</h4><p><a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer"><img src={logo} alt="TMDB" width="120" referrerPolicy="no-referrer" /></a> This product uses the TMDB API but is not endorsed or certified by TMDB. Watch-provider data: <a href="https://www.justwatch.com/" target="_blank" rel="noreferrer">JustWatch</a>.</p></section>;
}
