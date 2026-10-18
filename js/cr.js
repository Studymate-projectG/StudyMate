const crs = [
  ["CS 111", "Programming 1"],
  ["CS 112", "Programming 2"],
  ["CS 211", "Data Structures"],
  ["CS 221", "Discrete Mathematics"],
  ["CS 281", "Database Systems"],
  ["CS 311", "Algorithms"],
  ["CS 322", "Operating Systems"],
  ["CS 341", "Computer Networks"],
  ["CS 361", "Web Development"],
  ["CS 388T", "Agile Software Development"]
];

function cn(c) {
  const f = crs.find(x => x[0] == c);
  return f ? f[0] + " - " + f[1] : c;
}
