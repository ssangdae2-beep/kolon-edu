const express = require("express");
const noteService = require("../services/noteService");

const router = express.Router();

// GET /notes
router.get("/", (req, res) => {
  res.json(noteService.getAllNotes());
});

// GET /notes/:id
router.get("/:id", (req, res) => {
  const note = noteService.getNoteById(req.params.id);
  if (!note) return res.status(404).json({ error: "Note not found" });
  res.json(note);
});

// POST /notes
router.post("/", (req, res) => {
  const { title, content } = req.body;
  const note = noteService.createNote(title, content);
  res.status(201).json(note);
});

// DELETE /notes/:id
router.delete("/:id", (req, res) => {
  const deleted = noteService.deleteNote(req.params.id);
  if (!deleted) return res.status(404).json({ error: "Note not found" });
  res.status(204).send();
});

module.exports = router;
