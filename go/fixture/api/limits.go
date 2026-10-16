package api

// Limit returns a platform limit by name; see scripts/genlimits.
func Limit(name string) int {
	return limits[name]
}
