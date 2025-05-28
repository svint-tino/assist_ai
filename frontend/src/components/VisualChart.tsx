export function VisualChart({ url }: { url: string }) {
  console.log("Affichage du graphique :", url)
  return url ? (
    <iframe
      src={url}
      width={560}
      height={320}
      className="rounded border w-full visual-card-iframe"
      title="Visual chart"
    />
  ) : null
}

