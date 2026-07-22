export default function Loading() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-tv-bg text-foreground p-6">
      <div className="flex flex-col items-center space-y-4">
        {/* Animated Loading Ring */}
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent shadow-lg" />
        <div className="text-center">
          <p className="text-sm font-semibold tracking-wide text-foreground uppercase">
            Loading TradeCore...
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Initializing market feeds and strategy indicators
          </p>
        </div>
      </div>
    </div>
  );
}
