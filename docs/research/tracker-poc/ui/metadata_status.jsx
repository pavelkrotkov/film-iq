import React from "react";

export function MetadataUnavailable({cached}) {
  return <p>Film details are unknown: they may not have been loaded or may be unavailable{cached ? ", or the cache may have expired" : ""}. The synopsis field below is stored separately.</p>;
}
