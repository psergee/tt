// Code generated by "stringer -type=StateProvider -trimprefix StateProvider -linecomment"; DO NOT EDIT.

package replicaset

import "strconv"

func _() {
	// An "invalid array index" compiler error signifies that the constant values have changed.
	// Re-run the stringer command to generate them again.
	var x [1]struct{}
	_ = x[StateProviderUnknown-0]
	_ = x[StateProviderNone-1]
	_ = x[StateProviderTarantool-2]
	_ = x[StateProviderEtcd2-3]
}

const _StateProvider_name = "unknownnonetarantooletcd2"

var _StateProvider_index = [...]uint8{0, 7, 11, 20, 25}

func (i StateProvider) String() string {
	if i < 0 || i >= StateProvider(len(_StateProvider_index)-1) {
		return "StateProvider(" + strconv.FormatInt(int64(i), 10) + ")"
	}
	return _StateProvider_name[_StateProvider_index[i]:_StateProvider_index[i+1]]
}
