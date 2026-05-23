param(
  [string]$Api = "http://127.0.0.1:8010"
)

$ErrorActionPreference = "Stop"

function Invoke-SmokeWebRequest {
  param(
    [string]$Uri,
    [string]$Method = "Get",
    [string]$ContentType,
    [string]$Body
  )

  $parameters = @{
    Uri = $Uri
    Method = $Method
    UseBasicParsing = $true
  }
  if ($ContentType) {
    $parameters.ContentType = $ContentType
  }
  if ($Body) {
    $parameters.Body = $Body
  }

  try {
    return Invoke-WebRequest @parameters
  } catch {
    if ($_.Exception.Response) {
      $response = $_.Exception.Response
      $reader = [System.IO.StreamReader]::new($response.GetResponseStream())
      $content = $reader.ReadToEnd()
      return [PSCustomObject]@{
        StatusCode = [int]$response.StatusCode
        Content = $content
        Headers = $response.Headers
        RawContentLength = $content.Length
      }
    }
    throw
  }
}

$health = Invoke-RestMethod -Uri "$Api/health"
if ($health.status -ne "ok") {
  throw "API health check failed"
}
$readyResponse = Invoke-SmokeWebRequest -Uri "$Api/ready"
if ($readyResponse.StatusCode -ne 200 -and $readyResponse.StatusCode -ne 503) {
  throw "API ready check failed with status $($readyResponse.StatusCode)"
}
$ready = $readyResponse.Content | ConvertFrom-Json
if (-not $ready.checks.data_dir_writable) {
  throw "API data directory is not writable"
}
if (-not $ready.checks.store_persistence_ok) {
  throw "Store persistence check failed"
}
$config = Invoke-RestMethod -Uri "$Api/api/dev/config"

$reset = Invoke-RestMethod -Method Post -Uri "$Api/api/dev/reset"
if ($reset.status -ne "reset") {
  throw "Reset failed"
}

$tripBody = @{
  destination = "Hangzhou West Lake"
  duration_minutes = 120
  preferences = @("scenery", "video", "easy")
  use_panorama_camera = $true
} | ConvertTo-Json

$trip = Invoke-RestMethod -Method Post -Uri "$Api/api/trips" -ContentType "application/json" -Body $tripBody
$route = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/route"
$media = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/media/demo"
$frames = Invoke-RestMethod -Method Post -Uri "$Api/api/media/$($media.media_id)/extract-frames"
$marked = Invoke-RestMethod -Method Post -Uri "$Api/api/frames/$($frames.frames[-1].frame_id)/mark" -ContentType "application/json" -Body (@{ marked = $true; reason = "favorite moment" } | ConvertTo-Json)

$companionBody = @{
  frame_id = $frames.frames[0].frame_id
  route_node_id = $route.nodes[0].id
  user_status = "normal"
} | ConvertTo-Json

$companion = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/companion/analyze" -ContentType "application/json" -Body $companionBody
$export = Invoke-RestMethod -Method Post -Uri "$Api/api/trips/$($trip.trip_id)/exports"
$manifestResponse = Invoke-SmokeWebRequest -Uri "$Api/api/exports/$($export.export_id)/manifest"
$manifest = $manifestResponse.Content | ConvertFrom-Json
$bundleResponse = Invoke-SmokeWebRequest -Uri "$Api/api/exports/$($export.export_id)/bundle"
$trips = Invoke-RestMethod -Uri "$Api/api/trips?limit=3"

if ($manifest.schema -ne "panorama-companion.export-manifest.v1") {
  throw "Manifest schema mismatch"
}
if ($bundleResponse.Headers["Content-Type"] -notmatch "application/zip") {
  throw "Bundle response is not a ZIP"
}
if ($trips.Count -lt 1 -or $trips[0].trip_id -ne $trip.trip_id) {
  throw "Trip resume list did not include smoke trip"
}

[PSCustomObject]@{
  Health = $health.status
  Ready = $ready.status
  AiMode = $config.ai_mode
  MapMode = $config.map_mode
  Persistence = $config.store_persistence_enabled
  TripId = $trip.trip_id
  RouteNodes = $route.nodes.Count
  Frames = $frames.frames.Count
  MarkedFrame = $marked.marked
  CompanionLength = $companion.message.Length
  SelectedFrames = $export.selected_frames.Count
  DraftShots = $export.video_draft.Count
  FirstShotType = $export.video_draft[0].shot_type
  StoryEvents = $export.story_events.Count
  ManifestSchema = $manifest.schema
  BundleBytes = $bundleResponse.RawContentLength
  ResumeTrips = $trips.Count
}
